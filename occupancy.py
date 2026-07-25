import copy
import datetime
import io

# Set backend to non-gui 'Agg' BEFORE importing pyplot
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from common import DOW, ScheduleEvent

SLOT_MINUTES = 15 
SLOTS_PER_HOUR = 60 // SLOT_MINUTES
TOTAL_SLOTS = (24 * 60) // SLOT_MINUTES

DAY_NAMES = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]


def time_to_slot(t: datetime.time) -> int:
    """Converts a datetime.time object to a slot index (0 to TOTAL_SLOTS-1)."""
    minutes = t.hour * 60 + t.minute + t.second / 60
    return int(minutes // SLOT_MINUTES)


def build_occupancy_matrix(
    events: list[tuple[DOW, ScheduleEvent]],
) -> np.ndarray:
    """Returns a (7, TOTAL_SLOTS) array where matrix[day, slot] = count of active events."""
    matrix = np.zeros((7, TOTAL_SLOTS), dtype=int)

    for dow, event in events:
        start_slot = time_to_slot(event.start)
        stop_slot = time_to_slot(event.stop)

        # Handle edge cases where event ends at midnight or has zero length
        if stop_slot <= start_slot:
            stop_slot = TOTAL_SLOTS

        matrix[dow, start_slot:stop_slot] += 1

    return matrix.T


def generate_occupancy_figure(
        events: list[tuple[DOW, ScheduleEvent]], 
        buffer: io.BytesIO,
        dows: list[DOW],
        start: datetime.time,
        stop: datetime.time,
    ):

    matrix = build_occupancy_matrix(events)
    matrix = matrix[:, [n in dows for n in range(7)]]
    
    day_ticks = np.asarray(dows)
    day_labels = [DAY_NAMES[dow] for dow in dows]
    fig, ax = plt.subplots(figsize=(14, 4))

    my_cmap = copy.copy(plt.colormaps['YlOrRd'])
    my_cmap.set_under('white')

    cax = ax.imshow(matrix, cmap=my_cmap, aspect="auto", interpolation="nearest", vmin=0.0001)

    hour_ticks = np.arange(0, TOTAL_SLOTS, SLOTS_PER_HOUR)
    hour_labels = [f"{h:02d}:00" for h in range(24)]

    ax.set_xticks(day_ticks)
    ax.set_xticklabels(day_labels)

    ax.set_yticks(hour_ticks)
    ax.set_yticklabels(hour_labels)
    
    ax.set_ylim(
        time_to_slot(stop.replace(minute=0, second=0, microsecond=0)),
        time_to_slot(start.replace(minute=0, second=0, microsecond=0))
    )
    ax.set_title("Ocupación", fontsize=14, pad=12)
    ax.set_ylabel("Hora")
    ax.set_xlabel("Dia")

    cbar = fig.colorbar(cax, ax=ax, orientation="vertical", pad=0.02)
    cbar.set_label("Cantidad de cursos")

    plt.tight_layout()
    plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")

    # Clean up memory figures explicitly
    plt.close(fig)

    # Move cursor to the start of the BytesIO buffer
    buffer.seek(0)
    return buffer
# Leafy AI Basil Slot Vision V4

This version replaces unstable automatic clustering with fixed plant identities.

## Why

Connected components and watershed can fail when:
- two basil canopies touch,
- a large plant overlaps a small plant,
- leaves move,
- a plant becomes much larger over time.

In the real NFT farm, plant positions are known. V4 uses that information.

## Workflow

1. Run the program.
2. Select the whole growing zone.
3. Click the centre/base position of every planted basil.
4. Press Enter.
5. Each plant receives a permanent ID and permanent nearest-centre zone.
6. Detection runs continuously.
7. Press K only when you want pixel dimensions converted into cm.

## Run

```powershell
python .\basil_slot_vision_v4.py --source 0
```

## Register plants

When asked:
- left click each basil planting position,
- right click to undo the last point,
- C clears,
- Enter/Space finishes.

The displayed count is the number of registered/planted basil positions.

## Controls

- R: reselect growing zone
- S: re-register plant centres
- K: calibrate known-width reference
- G: optional empty-background capture
- N: clear background filter
- V: show/hide plant-zone boundaries
- M: show/hide green mask
- P: snapshot
- Space: pause/resume
- Q/Esc: quit

## Why this behaves better when plants touch

Each pixel in the growing zone belongs permanently to the nearest registered
plant centre. Therefore two canopies touching does not merge their identities.

This is similar to using known planting slots in the real farm.

## Important limitation

If one plant physically hides another from the camera, the hidden foliage cannot
be measured from one RGB image. The plant's identity/count remains known, but
visible canopy size may be underestimated.

For mature overlapping basil, canopy coverage per fixed planting slot is more
reliable than trying to infer exact individual width from free-form bounding boxes.

# Die Hard Trilogy — separate Die Hard 2 patches

## Required image

Apply to **Die Hard Trilogy (USA) (v1.1) (Track 01).bin**, with the existing
**Nuvee USA Greatest Hits GunCon conversion already applied**, as used in this
project. These are additional patches; they do not install the original
GunCon conversion. Other regions/revisions and clean, unconverted images
are not supported by this release.

Exact starting Track 01 SHA-256:

`1a2f348289285ad95cbaed49ffb535cc0d3792307a9a7d6c66fa6c486cdef3a1`

## Choose your patches

| File | Changes |
| --- | --- |
| Gun Patch Mister.ppf | Moves shots 13 game-coordinate units left and 6 down, relative to the original GunCon conversion. Candidate based on the latest MiSTer green-circle illustration; still requires a hardware test. |
| Gun Patch Emulator.ppf | Moves shots 13 game-coordinate units left and 6 up. Tested and accepted in DuckStation with the user's setup. |
| Die Hard 2 UI Patch.ppf | Corrected health badge proportions; smaller rocket/grenade symbols and counters at bottom left; smaller score centered near the top; controller-mode symbol removed. Accepted during the DuckStation tests. |

Use **one aiming patch**, optionally together with the UI patch. The UI patch
can also be used alone on the required base image. UI and aiming patches may
be applied in either order. Do not stack MiSTer and emulator aiming patches.
The fixed offsets are setup-specific; this release does not add calibration
or an offset menu.

## Applying

1. Make a copy of your existing GunCon-patched Track 01 BIN.
2. Apply the chosen `.ppf` file(s) to that copy using a PPF3-compatible patcher.
   Select the BIN, not the CUE, CHD, or another audio track.
3. Keep the other tracks and CUE together with the patched BIN. If you rename
   the BIN, update its filename in the CUE.
4. Start the game from a fresh boot. An old savestate can restore the old
   executable in RAM and hide the disc changes. Normal memory-card saves can
   still be used.
5. Test MiSTer aim before treating that candidate offset as final.

For CHD use, patch the BIN first, then rebuild the CHD from its CUE.

## Undo and switching

Each PPF includes undo data. Use your patcher's undo operation or return to
your backup. To switch aiming profiles, undo the current aiming patch before
applying the other, or start again from the base-image copy. The UI patch is
independent and can remain applied.

## Validation

Generated files were parsed back and applied to the original affected sectors.
Every executable edit and regenerated EDC/ECC was checked, then every patch
was undone back to the exact original bytes. UI plus each aiming profile was
verified in both application orders. Their affected sectors do not overlap.
The source BIN's SHA-256 was unchanged after building.

`Verification.json` records patch hashes, offsets, and validation results.
This verifies the patch files; MiSTer hardware gameplay remains untested.
UI and emulator behavior were tested live in RAM before packaging.

PPF3 encoding follows the original
[MakePPF3 source](https://github.com/Sappharad/MultiPatch/blob/master/ppfdev/makeppf3_linux.c),
including block checking and undo records.

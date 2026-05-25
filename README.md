# ABC Font Editor
### A desktop GUI tool for viewing and editing .abc binary font files from the FlatOut game series (FlatOut, FlatOut 2, FlatOut: Ultimate Carnage, FlatOut: Head On).

## Features
- Load & visualize .abc font files alongside their texture atlases (.dds / .png), with glyph rectangles drawn as overlays on the texture
- Export to JSON — dump all glyph records with UV or pixel coordinates, character mappings, padding, and width metadata
- Import from JSON — apply edited glyph data back into memory and save as a new .abc file
- Add / delete symbols — add new glyphs or remove existing ones by character, Unicode codepoint (U+XXXX), or hex value, with automatic charmap updates
- Manual offset control — adjust the binary offset used to parse glyph records, useful for reverse-engineering unknown file variants
- Configurable texture resolution — set texture dimensions manually for correct pixel coordinate calculation when no texture file is loaded
- Zoom — zoom in/out on the texture canvas from 10% to 300%

<p align="center">
  <img src="Screenshot.png" width="768">
</p>

## Requirements
- Python 3.x
- PyQt5
- Pillow

## Usage
```bash
pip install PyQt5 Pillow
python abc_font_editor.py
```

## Usage Examples
1. Viewing a font file
    1. Click Load Texture and open the font texture (e.g. hud_numbers.dds)
    2. Click Load .abc and open the matching font file (e.g. hud_numbers.abc)
    3. Green rectangles will appear on the texture, each marking a glyph's position. The glyph index is shown in the top-left corner of each rectangle.

2. Exporting glyph data for editing
    1. Load the .abc file (texture is optional)
    2. Click Export to JSON
    3. Choose coordinate format — UV (normalized 0.0–1.0) or Pixel (absolute pixels)
    4. Save the .json file and open it in any text editor

Example exported glyph entry:
```json
{
    "index": 5,
    "chars": ["A"],
    "codepoints": [65],
    "px_x_start": 12,
    "px_y_start": 0,
    "px_x_end": 28,
    "px_y_end": 32,
    "padding_left": 1,
    "glyph_width": 15,
    "cell_width": 17
}
```
3. Importing edited glyphs back
    1. Edit the exported .json file (e.g. adjust px_x_start / px_x_end to remap a glyph to a new position on the texture)
    2. Click Import from JSON and select your edited file
    3. Click Save .abc to write the result to disk

4. Adding a new symbol
    1. Load an .abc file
    2. Click Add Symbol
    3. Enter the character or codepoint (e.g. Ж or U+0416) and fill in the pixel coordinates and width values
    4. Click Save .abc to save

5. Deleting symbols
    1. Load an .abc file
    2. Click Delete Symbols
    3. Enter the characters or codepoints to remove — you can use:
        - Single characters: A B C
        - Unicode notation: U+0041 U+0042
        - Ranges: A-Z or U+0041-U+005A
    4. Confirm — the charmap and glyph table will be updated automatically
    5. Click Save .abc to save

6. Working without a texture
If you don't have the texture file, you can still load and edit the .abc data. Set the correct texture resolution manually (e.g. 2048 x 1024) and click Apply — pixel coordinates will be calculated correctly for export

# Basic Drive Audit Tool (BDAT)

A small Windows tool that audits every hard drive on your PC and lists the following in a table:

Drive Letter, Drive Name, Total Size, Size Used, Size Free, File Count, Folder Count, and File and Folder Count.

Results can be exported to CSV.

<img width="1318" height="567" alt="BDAT" src="https://github.com/user-attachments/assets/f26ab041-32fb-4d6e-8f80-c0311d8845ae" />

## Run from source

Requires Windows 10 and Python 3.8 or newer. No extra packages are needed.

```
python drive-audit.py
```

## Build an exe

Double-click `build-exe.bat`. The finished file is saved in the `dist` folder as `Basic Drive Audit Tool.exe`.

`make-icon.py` recreates `drive-audit.ico` if you want to change the icon (needs Pillow).

## Notes

- Sizes follow the Windows convention (1 GB is 1024 MB), so they match File Explorer.
- Junctions and symbolic links are skipped so nothing is counted twice.
- Folders that Windows blocks are skipped, so counts on system drives can differ slightly from Explorer.

## Credit

Created by CASK.exe - https://github.com/Caskexe

Repository: https://github.com/Caskexe/Basic-Drive-Audit-Tool

## Licence

MIT. See the `LICENSE` file.

## Support My Work

Donations are optional, and there is no expectation to give. If you find my tools useful and want to say thanks, these are the easiest ways to do it:

- [Ko-fi](https://ko-fi.com/caskexe)
- [Buy Me a Coffee](https://buymeacoffee.com/caskexe)
- [PayPal](https://www.paypal.com/donate/?hosted_button_id=TGX3Q6GHFVZXU)

**Crypto**

- Litecoin (LTC): `MLopHqV7ZBXW67ey4DPMhGWGa3pGan5ZSJ`
- Bitcoin (BTC): `3GaR1skLQapxSvaCSMaJNvQr9QD3rbp1AR`

**Music**

If you enjoy synthwave, retrowave or 80s pop, you can listen to and buy my music on Bandcamp:

- [HELIXIRx](https://helixirx.bandcamp.com/)
- [Empty Triangles](https://emptytriangles.bandcamp.com/)
- [Sunsetron](https://sunsetron.bandcamp.com/)

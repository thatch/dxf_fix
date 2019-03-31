# dxf\_fix

This uses ezdxf load dxf files, connect individal LINE segments into POLYLINE,
and correct their direction based on nesting level (assuming that it represents
a 2d shape).

Requirements:

* Python 2.7 or 3+
* `ezdxf`

## Usage

`dxf_fix in.dxf [ -o out.dxf ]` will write `out.dxf` if provided, otherwise `in.dxf.new`

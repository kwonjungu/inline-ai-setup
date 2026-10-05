# 한 파일을 PDF로 바꾼다 (별도 프로세스로 실행). 사용: python render_child.py <kind> <src> <pdf>
import sys, os, time
kind, src, pdf = sys.argv[1], sys.argv[2], sys.argv[3]
import pythoncom
pythoncom.CoInitialize()
import win32com.client.dynamic as d

if kind in ("hwp", "hwpx"):
    h = d.Dispatch("HWPFrame.HwpObject")
    try:
        h.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    except Exception:
        pass
    h.SetMessageBoxMode(0x00020021)
    ok = h.Open(src, "HWPX" if kind == "hwpx" else "HWP", "forceopen:true")
    if not ok:
        print("open fail");
    h.SaveAs(pdf, "PDF", "")
    try:
        h.Clear(1)
    except Exception:
        pass
    h.Quit()
elif kind == "xlsx":
    x = d.Dispatch("Excel.Application")
    x.Visible = False
    x.DisplayAlerts = False
    wb = x.Workbooks.Open(src, 0, False)
    x.CalculateFull()
    for ws in wb.Worksheets:
        try:
            ps = ws.PageSetup
            ps.Zoom = False
            ps.FitToPagesWide = 1
            ps.FitToPagesTall = False
            ps.Orientation = 2 if ws.UsedRange.Columns.Count > 8 else 1
        except Exception as e:
            print("pagesetup", e)
    wb.Worksheets(1).Activate()
    wb.ExportAsFixedFormat(0, pdf)
    wb.Close(False)
    x.Quit()
elif kind == "pptx":
    p = d.Dispatch("PowerPoint.Application")
    pres = p.Presentations.Open(src, True, False, False)
    pres.SaveAs(pdf, 32)
    pres.Close()
    p.Quit()
print("ok" if os.path.exists(pdf) else "nopdf")

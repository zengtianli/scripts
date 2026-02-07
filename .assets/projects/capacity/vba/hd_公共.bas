' ============================================================
' 模块名称: Module_公共
' 功能描述: 公共工具函数
' 创建日期: 2025-01-19
' 作者: 开发部
' ============================================================

Option Explicit

' 颜色常量
Public Const COLOR_AUTO As Long = 10284031   ' RGB(255, 235, 156) 淡黄色
Public Const UNIT_FACTOR As Double = 31.536  ' 单位换算系数（秒→年，mg→t）

' ============================================================
' 检查 Sheet 是否存在
' ============================================================
Public Function SheetExists(sheetName As String) As Boolean
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets(sheetName)
    SheetExists = Not ws Is Nothing
    On Error GoTo 0
End Function

' ============================================================
' 获取或创建 Sheet
' ============================================================
Public Function GetOrCreateSheet(sheetName As String, Optional afterSheet As Worksheet = Nothing) As Worksheet
    Dim ws As Worksheet
    
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets(sheetName)
    On Error GoTo 0
    
    If ws Is Nothing Then
        If afterSheet Is Nothing Then
            Set ws = ThisWorkbook.Sheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
        Else
            Set ws = ThisWorkbook.Sheets.Add(After:=afterSheet)
        End If
        ws.Name = sheetName
    End If
    
    Set GetOrCreateSheet = ws
End Function

' ============================================================
' 获取最后一行
' ============================================================
Public Function GetLastRow(ws As Worksheet, col As Long) As Long
    GetLastRow = ws.Cells(ws.Rows.Count, col).End(xlUp).Row
End Function

' ============================================================
' 获取最后一列
' ============================================================
Public Function GetLastCol(ws As Worksheet, Row As Long) As Long
    GetLastCol = ws.Cells(Row, ws.Columns.Count).End(xlToLeft).Column
End Function

' ============================================================
' 安全读取数值（避免空值或非数字报错）
' ============================================================
Public Function SafeDouble(val As Variant, Optional defaultVal As Double = 0) As Double
    On Error Resume Next
    If IsEmpty(val) Or IsNull(val) Or val = "" Then
        SafeDouble = defaultVal
    Else
        SafeDouble = CDbl(val)
    End If
    On Error GoTo 0
End Function

' ============================================================
' 安全读取整数
' ============================================================
Public Function SafeLong(val As Variant, Optional defaultVal As Long = 0) As Long
    On Error Resume Next
    If IsEmpty(val) Or IsNull(val) Or val = "" Then
        SafeLong = defaultVal
    Else
        SafeLong = CLng(val)
    End If
    On Error GoTo 0
End Function

' ============================================================
' 安全读取字符串
' ============================================================
Public Function SafeString(val As Variant, Optional defaultVal As String = "") As String
    On Error Resume Next
    If IsEmpty(val) Or IsNull(val) Then
        SafeString = defaultVal
    Else
        SafeString = Trim(CStr(val))
    End If
    On Error GoTo 0
End Function

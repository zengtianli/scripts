' ============================================================
' 模块名称: sk_公共
' 功能描述: 水库纳污能力计算 - 公共工具函数
' 创建日期: 2025-01-20
' 作者: 开发部
' ============================================================

Option Explicit

' 颜色常量
Public Const SK_COLOR_AUTO As Long = 10284031   ' RGB(255, 235, 156) 淡黄色
Public Const SK_UNIT_FACTOR As Double = 31.536  ' 单位换算系数（秒→年，mg→t）

' ============================================================
' 检查 Sheet 是否存在
' ============================================================
Public Function SK_SheetExists(sheetName As String) As Boolean
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets(sheetName)
    SK_SheetExists = Not ws Is Nothing
    On Error GoTo 0
End Function

' ============================================================
' 获取或创建 Sheet
' ============================================================
Public Function SK_GetOrCreateSheet(sheetName As String, Optional afterSheet As Worksheet = Nothing) As Worksheet
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
    
    Set SK_GetOrCreateSheet = ws
End Function

' ============================================================
' 获取最后一行
' ============================================================
Public Function SK_GetLastRow(ws As Worksheet, col As Long) As Long
    SK_GetLastRow = ws.Cells(ws.Rows.Count, col).End(xlUp).Row
End Function

' ============================================================
' 获取最后一列
' ============================================================
Public Function SK_GetLastCol(ws As Worksheet, Row As Long) As Long
    SK_GetLastCol = ws.Cells(Row, ws.Columns.Count).End(xlToLeft).Column
End Function

' ============================================================
' 安全读取数值
' ============================================================
Public Function SK_SafeDouble(val As Variant, Optional defaultVal As Double = 0) As Double
    On Error Resume Next
    If IsEmpty(val) Or IsNull(val) Or val = "" Then
        SK_SafeDouble = defaultVal
    Else
        SK_SafeDouble = CDbl(val)
    End If
    On Error GoTo 0
End Function

' ============================================================
' 安全读取整数
' ============================================================
Public Function SK_SafeLong(val As Variant, Optional defaultVal As Long = 0) As Long
    On Error Resume Next
    If IsEmpty(val) Or IsNull(val) Or val = "" Then
        SK_SafeLong = defaultVal
    Else
        SK_SafeLong = CLng(val)
    End If
    On Error GoTo 0
End Function

' ============================================================
' 安全读取字符串
' ============================================================
Public Function SK_SafeString(val As Variant, Optional defaultVal As String = "") As String
    On Error Resume Next
    If IsEmpty(val) Or IsNull(val) Then
        SK_SafeString = defaultVal
    Else
        SK_SafeString = Trim(CStr(val))
    End If
    On Error GoTo 0
End Function

' ============================================================
' 获取水文年月份名称（4月→3月）
' ============================================================
Public Function SK_GetHydroMonthName(monthIdx As Long) As String
    ' monthIdx: 1=4月, 2=5月, ..., 9=12月, 10=1月, 11=2月, 12=3月
    Dim realMonth As Long
    realMonth = ((monthIdx + 2) Mod 12) + 1
    If realMonth = 0 Then realMonth = 12
    
    ' 修正计算
    realMonth = monthIdx + 3
    If realMonth > 12 Then realMonth = realMonth - 12
    
    SK_GetHydroMonthName = realMonth & "月"
End Function

' ============================================================
' 获取水文年月份索引（1-12对应4月-3月）
' ============================================================
Public Function SK_GetHydroMonthIdx(calendarMonth As Long) As Long
    ' 输入: 日历月份 1-12
    ' 输出: 水文年月份索引 1-12 (1=4月, 12=3月)
    If calendarMonth >= 4 Then
        SK_GetHydroMonthIdx = calendarMonth - 3
    Else
        SK_GetHydroMonthIdx = calendarMonth + 9
    End If
End Function

' ============================================================
' 获取水文年（4月起算）
' ============================================================
Public Function SK_GetHydroYear(dt As Date) As Long
    Dim y As Long, m As Long
    y = Year(dt)
    m = Month(dt)
    
    ' 1-3月属于上一水文年
    If m < 4 Then
        SK_GetHydroYear = y - 1
    Else
        SK_GetHydroYear = y
    End If
End Function

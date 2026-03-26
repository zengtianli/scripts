' ============================================================
' 模块名称: sk_输入准备
' 功能描述: 水库纳污能力计算 - 输入表生成和管理
' 创建日期: 2025-01-20
' 作者: 开发部
' ============================================================
'
' 输入表布局（水库功能区-输入）:
'   行1: 功能区数量(B1), 功能区编号(D1起)
'   行2: 方案个数(B2), 功能区名
'   行3: Cs
'   行4: K(1/s)
'   行5: b
' ============================================================

Option Explicit

' 行号常量
Private Const ROW_ZONE_COUNT As Long = 1      ' 功能区数量
Private Const ROW_SCHEME_COUNT As Long = 2    ' 方案个数 / 功能区名
Private Const ROW_CS As Long = 3              ' Cs
Private Const ROW_K As Long = 4               ' K(1/s)
Private Const ROW_B As Long = 5               ' b

' ============================================================
' 初始化输入表 - 按钮1
' ============================================================
Public Sub SK_初始化输入表()
    On Error GoTo ErrorHandler
    
    Dim ws As Worksheet
    
    ' 获取或创建 Sheet
    Set ws = SK_GetOrCreateSheet("水库功能区-输入")
    ws.Activate
    
    Application.ScreenUpdating = False
    
    ' 清除旧数据
    ws.Cells.Clear
    
    ' A列说明
    ws.Cells(ROW_ZONE_COUNT, 1).Value = "功能区数量 →"
    ws.Cells(ROW_SCHEME_COUNT, 1).Value = "方案个数 →"
    ws.Range("A1:A2").HorizontalAlignment = xlRight
    
    ' B列（用户填写）
    ws.Cells(ROW_ZONE_COUNT, 2).Value = ""
    ws.Cells(ROW_SCHEME_COUNT, 2).Value = ""
    ws.Range("B1:B2").Interior.Color = RGB(255, 255, 200)  ' 浅黄色表示需填写
    
    ' D列标签
    ws.Cells(ROW_ZONE_COUNT, 4).Value = "功能区编号 →"
    ws.Cells(ROW_SCHEME_COUNT, 4).Value = "功能区名"
    ws.Cells(ROW_CS, 4).Value = "Cs"
    ws.Cells(ROW_K, 4).Value = "K(1/s)"
    ws.Cells(ROW_B, 4).Value = "b"
    ws.Range("D1:D5").HorizontalAlignment = xlRight
    
    ' 设置列宽
    ws.Columns("A").ColumnWidth = 14
    ws.Columns("B").ColumnWidth = 8
    ws.Columns("C").ColumnWidth = 2
    ws.Columns("D").ColumnWidth = 14
    
    Application.ScreenUpdating = True
    
    MsgBox "水库输入表初始化完成！" & vbCrLf & vbCrLf & _
           "请填写：" & vbCrLf & _
           "1. B1 = 功能区数量" & vbCrLf & _
           "2. B2 = 方案个数" & vbCrLf & vbCrLf & _
           "然后点击「生成功能区列」", vbInformation, "完成"
    Exit Sub
    
ErrorHandler:
    Application.ScreenUpdating = True
    MsgBox "出错：" & Err.Description, vbCritical, "错误"
End Sub

' ============================================================
' 生成功能区列 - 按钮2
' ============================================================
Public Sub SK_生成功能区列()
    On Error GoTo ErrorHandler
    
    Dim ws As Worksheet
    Set ws = ActiveSheet
    
    ' 读取功能区数量
    Dim zoneCount As Long
    zoneCount = SK_SafeLong(ws.Cells(ROW_ZONE_COUNT, 2).Value)
    
    If zoneCount <= 0 Then
        MsgBox "请先在 B1 单元格填入功能区数量（大于0的整数）", vbExclamation, "提示"
        Exit Sub
    End If
    
    If zoneCount > 100 Then
        MsgBox "功能区数量不能超过100", vbExclamation, "提示"
        Exit Sub
    End If
    
    Application.ScreenUpdating = False
    
    ' 清除旧的功能区列（从E列开始）
    Dim lastCol As Long
    lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    If lastCol >= 5 Then
        ws.Range(ws.Cells(1, 5), ws.Cells(10, lastCol)).ClearContents
        ws.Range(ws.Cells(1, 5), ws.Cells(10, lastCol)).Interior.ColorIndex = xlNone
    End If
    
    ' 确保D列标签存在
    ws.Cells(ROW_ZONE_COUNT, 4).Value = "功能区编号 →"
    ws.Cells(ROW_SCHEME_COUNT, 4).Value = "功能区名"
    ws.Cells(ROW_CS, 4).Value = "Cs"
    ws.Cells(ROW_K, 4).Value = "K(1/s)"
    ws.Cells(ROW_B, 4).Value = "b"
    
    ' 生成功能区列标题（从E列开始）
    Dim i As Long
    For i = 1 To zoneCount
        ws.Cells(ROW_ZONE_COUNT, 4 + i).Value = "功能区" & i
        ws.Cells(ROW_ZONE_COUNT, 4 + i).Interior.Color = SK_COLOR_AUTO
        ws.Columns(4 + i).ColumnWidth = 12
        
        ' 高亮需填写的单元格
        ws.Range(ws.Cells(ROW_SCHEME_COUNT, 4 + i), ws.Cells(ROW_B, 4 + i)).Interior.Color = RGB(255, 255, 200)
    Next i
    
    Application.ScreenUpdating = True
    
    MsgBox "已生成 " & zoneCount & " 个功能区列" & vbCrLf & vbCrLf & _
           "请填入每个功能区的：" & vbCrLf & _
           "- 第2行：功能区名（如：青山水库）" & vbCrLf & _
           "- 第3行：Cs 目标浓度(mg/L)" & vbCrLf & _
           "- 第4行：K 衰减系数(1/s)" & vbCrLf & _
           "- 第5行：b 不均匀系数" & vbCrLf & vbCrLf & _
           "填好后点击「生成基础信息」", vbInformation, "完成"
    Exit Sub
    
ErrorHandler:
    Application.ScreenUpdating = True
    MsgBox "出错：" & Err.Description, vbCritical, "错误"
End Sub

' ============================================================
' 清除输入 - 按钮6
' ============================================================
Public Sub SK_清除输入()
    On Error GoTo ErrorHandler
    
    Dim ws As Worksheet
    Set ws = ActiveSheet
    
    ' 确认操作
    Dim result As VbMsgBoxResult
    result = MsgBox("确定要清除所有输入数据吗？", vbYesNo + vbQuestion, "确认清除")
    
    If result <> vbYes Then Exit Sub
    
    Application.ScreenUpdating = False
    
    ' 获取数据范围
    Dim lastCol As Long, lastRow As Long
    lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    lastRow = ws.Cells(ws.Rows.Count, 4).End(xlUp).Row
    
    If lastCol < 5 Then lastCol = 5
    If lastRow < 5 Then lastRow = 5
    
    ' 清除 E 列起的内容和背景色
    ws.Range(ws.Cells(1, 5), ws.Cells(lastRow + 5, lastCol)).ClearContents
    ws.Range(ws.Cells(1, 5), ws.Cells(lastRow + 5, lastCol)).Interior.ColorIndex = xlNone
    
    Application.ScreenUpdating = True
    
    MsgBox "已清除所有输入数据", vbInformation, "完成"
    Exit Sub
    
ErrorHandler:
    Application.ScreenUpdating = True
    MsgBox "出错：" & Err.Description, vbCritical, "错误"
End Sub

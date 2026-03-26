' ============================================================
' 模块名称: Module_输入准备
' 功能描述: 功能区输入表的生成和管理
' 创建日期: 2025-01-19
' 作者: 开发部
' ============================================================
'
' 输入表布局（河道功能区-输入）:
'   行1: 功能区数量(B1), 功能区编号(D1起)
'   行2: 方案个数(B2), 功能区名
'   行3: Cs
'   行4: K(1/s)
'   行5: b
'   行6: a
'   行7: β
'   行8: 干流总长L(m)
'   行9: 干流C0
'   行10: 支流数量
'   行11: 干流名
'   行12起: 支流信息（每条支流5行：分隔行、名称、长度、汇入位置、浓度）
' ============================================================

Option Explicit

' 行号常量
Private Const ROW_ZONE_COUNT As Long = 1      ' 功能区数量
Private Const ROW_SCHEME_COUNT As Long = 2    ' 方案个数 / 功能区名
Private Const ROW_CS As Long = 3              ' Cs
Private Const ROW_K As Long = 4               ' K(1/s)
Private Const ROW_B As Long = 5               ' b
Private Const ROW_A As Long = 6               ' a
Private Const ROW_BETA As Long = 7            ' β
Private Const ROW_MAIN_LENGTH As Long = 8     ' 干流总长L(m)
Private Const ROW_MAIN_C0 As Long = 9         ' 干流C0
Private Const ROW_BRANCH_COUNT As Long = 10   ' 支流数量
Private Const ROW_MAIN_NAME As Long = 11      ' 干流名
Private Const ROW_BRANCH_START As Long = 12   ' 支流信息起始行

' 每条支流占用的行数
Private Const ROWS_PER_BRANCH As Long = 5     ' 分隔行、名称、长度、汇入位置、浓度

' ============================================================
' 初始化输入表 - 按钮0（创建完整表结构）
' ============================================================
Public Sub 初始化输入表()
    On Error GoTo ErrorHandler
    
    Dim ws As Worksheet
    
    ' 检查是否存在，不存在则创建
    Set ws = GetOrCreateSheet("河道功能区-输入")
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
    
    ' C列空
    
    ' D列标签
    ws.Cells(ROW_ZONE_COUNT, 4).Value = "功能区编号 →"
    ws.Cells(ROW_SCHEME_COUNT, 4).Value = "功能区名"
    ws.Cells(ROW_CS, 4).Value = "Cs"
    ws.Cells(ROW_K, 4).Value = "K(1/s)"
    ws.Cells(ROW_B, 4).Value = "b"
    ws.Cells(ROW_A, 4).Value = "a"
    ws.Cells(ROW_BETA, 4).Value = "β"
    ws.Cells(ROW_MAIN_LENGTH, 4).Value = "干流总长L(m)"
    ws.Cells(ROW_MAIN_C0, 4).Value = "干流C0"
    ws.Cells(ROW_BRANCH_COUNT, 4).Value = "支流数量"
    ws.Cells(ROW_MAIN_NAME, 4).Value = "干流名"
    ws.Range("D1:D11").HorizontalAlignment = xlRight
    
    ' 设置列宽
    ws.Columns("A").ColumnWidth = 14
    ws.Columns("B").ColumnWidth = 8
    ws.Columns("C").ColumnWidth = 2
    ws.Columns("D").ColumnWidth = 16
    
    Application.ScreenUpdating = True
    
    MsgBox "输入表初始化完成！" & vbCrLf & vbCrLf & _
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
' 生成功能区列 - 按钮1
' ============================================================
Public Sub 生成功能区列()
    On Error GoTo ErrorHandler
    
    Dim ws As Worksheet
    Set ws = ActiveSheet
    
    ' 读取功能区数量
    Dim zoneCount As Long
    zoneCount = SafeLong(ws.Cells(ROW_ZONE_COUNT, 2).Value)  ' B1
    
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
        ws.Range(ws.Cells(1, 5), ws.Cells(50, lastCol)).ClearContents
        ws.Range(ws.Cells(1, 5), ws.Cells(50, lastCol)).Interior.ColorIndex = xlNone
    End If
    
    ' 确保D列标签存在
    ws.Cells(ROW_ZONE_COUNT, 4).Value = "功能区编号 →"
    ws.Cells(ROW_SCHEME_COUNT, 4).Value = "功能区名"
    ws.Cells(ROW_CS, 4).Value = "Cs"
    ws.Cells(ROW_K, 4).Value = "K(1/s)"
    ws.Cells(ROW_B, 4).Value = "b"
    ws.Cells(ROW_A, 4).Value = "a"
    ws.Cells(ROW_BETA, 4).Value = "β"
    ws.Cells(ROW_MAIN_LENGTH, 4).Value = "干流总长L(m)"
    ws.Cells(ROW_MAIN_C0, 4).Value = "干流C0"
    ws.Cells(ROW_BRANCH_COUNT, 4).Value = "支流数量"
    ws.Cells(ROW_MAIN_NAME, 4).Value = "干流名"
    
    ' 生成功能区列标题（从E列开始）
    Dim i As Long
    For i = 1 To zoneCount
        ws.Cells(ROW_ZONE_COUNT, 4 + i).Value = "功能区" & i
        ws.Cells(ROW_ZONE_COUNT, 4 + i).Interior.Color = COLOR_AUTO
        ws.Columns(4 + i).ColumnWidth = 12
        
        ' 高亮需填写的单元格
        ws.Range(ws.Cells(ROW_SCHEME_COUNT, 4 + i), ws.Cells(ROW_BRANCH_COUNT, 4 + i)).Interior.Color = RGB(255, 255, 200)
    Next i
    
    Application.ScreenUpdating = True
    
    MsgBox "已生成 " & zoneCount & " 个功能区列" & vbCrLf & vbCrLf & _
           "请填入每个功能区的：" & vbCrLf & _
           "- 第2行：功能区名（如：甬江干流）" & vbCrLf & _
           "- 第3-7行：Cs、K、b、a、β" & vbCrLf & _
           "- 第8行：干流总长L(m)" & vbCrLf & _
           "- 第9行：干流入口浓度C0" & vbCrLf & _
           "- 第10行：支流数量（0=无支流）" & vbCrLf & vbCrLf & _
           "填好后点击「生成干支流名」", vbInformation, "完成"
    Exit Sub
    
ErrorHandler:
    Application.ScreenUpdating = True
    MsgBox "出错：" & Err.Description, vbCritical, "错误"
End Sub

' ============================================================
' 生成干支流名 - 按钮2
' ============================================================
Public Sub 生成干支流名()
    On Error GoTo ErrorHandler
    
    Dim ws As Worksheet
    Set ws = ActiveSheet
    
    ' 读取功能区数量
    Dim zoneCount As Long
    zoneCount = SafeLong(ws.Cells(ROW_ZONE_COUNT, 2).Value)  ' B1
    
    If zoneCount <= 0 Then
        MsgBox "请先在 B1 单元格填入功能区数量", vbExclamation, "提示"
        Exit Sub
    End If
    
    Application.ScreenUpdating = False
    
    ' 读取各功能区的名称和支流数量
    Dim zoneNames() As String
    Dim branchCounts() As Long
    Dim maxBranch As Long
    
    ReDim zoneNames(1 To zoneCount)
    ReDim branchCounts(1 To zoneCount)
    maxBranch = 0
    
    Dim i As Long, col As Long
    
    For i = 1 To zoneCount
        col = 4 + i  ' E=5, F=6, ...
        zoneNames(i) = SafeString(ws.Cells(ROW_SCHEME_COUNT, col).Value)
        branchCounts(i) = SafeLong(ws.Cells(ROW_BRANCH_COUNT, col).Value)
        If branchCounts(i) < 0 Then branchCounts(i) = 0
        If branchCounts(i) > maxBranch Then maxBranch = branchCounts(i)
    Next i
    
    ' 检查是否有功能区名
    Dim hasName As Boolean
    hasName = False
    For i = 1 To zoneCount
        If Len(zoneNames(i)) > 0 Then
            hasName = True
            Exit For
        End If
    Next i
    
    If Not hasName Then
        Application.ScreenUpdating = True
        MsgBox "请先在第2行填入功能区名", vbExclamation, "提示"
        Exit Sub
    End If
    
    ' 清除旧的干支流信息（第11行及以下）
    Dim lastRow As Long, lastCol As Long
    lastRow = ws.Cells(ws.Rows.Count, 4).End(xlUp).Row
    lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    If lastRow >= ROW_MAIN_NAME Then
        ws.Range(ws.Cells(ROW_MAIN_NAME, 4), ws.Cells(lastRow + 20, lastCol)).ClearContents
        ws.Range(ws.Cells(ROW_MAIN_NAME, 4), ws.Cells(lastRow + 20, lastCol)).Interior.ColorIndex = xlNone
    End If
    
    ' 生成干流名（第11行）
    For i = 1 To zoneCount
        col = 4 + i
        If Len(zoneNames(i)) > 0 Then
            ws.Cells(ROW_MAIN_NAME, col).Value = zoneNames(i) & "-0"
            ws.Cells(ROW_MAIN_NAME, col).Interior.Color = COLOR_AUTO
        End If
    Next i
    
    ' 生成支流信息（每条支流5行）
    Dim j As Long, baseRow As Long
    
    For j = 1 To maxBranch
        baseRow = ROW_BRANCH_START + (j - 1) * ROWS_PER_BRANCH
        
        ' D列标签
        ws.Cells(baseRow, 4).Value = "─支流" & j & "─"
        ws.Cells(baseRow + 1, 4).Value = "支流" & j & "名"
        ws.Cells(baseRow + 2, 4).Value = "支流" & j & "长度L(m)"
        ws.Cells(baseRow + 3, 4).Value = "支流" & j & "汇入位置(m)"
        ws.Cells(baseRow + 4, 4).Value = "支流" & j & "浓度C0"
        
        ' 各功能区的支流名
        For i = 1 To zoneCount
            col = 4 + i
            If branchCounts(i) >= j And Len(zoneNames(i)) > 0 Then
                ws.Cells(baseRow + 1, col).Value = zoneNames(i) & "-" & j
                ws.Cells(baseRow + 1, col).Interior.Color = COLOR_AUTO
            End If
        Next i
    Next j
    
    Application.ScreenUpdating = True
    
    MsgBox "干支流名生成完成！" & vbCrLf & vbCrLf & _
           "干流：" & zoneCount & " 个" & vbCrLf & _
           "最大支流数：" & maxBranch & " 条" & vbCrLf & vbCrLf & _
           "请填入各支流的：" & vbCrLf & _
           "- 长度L(m)" & vbCrLf & _
           "- 汇入位置(m) ← 在干流的第几米汇入" & vbCrLf & _
           "- 浓度C0", vbInformation, "完成"
    Exit Sub
    
ErrorHandler:
    Application.ScreenUpdating = True
    MsgBox "出错：" & Err.Description, vbCritical, "错误"
End Sub

' ============================================================
' 清除输入 - 按钮3
' ============================================================
Public Sub 清除输入()
    On Error GoTo ErrorHandler
    
    Dim ws As Worksheet
    Set ws = ActiveSheet
    
    ' 确认操作
    Dim result As VbMsgBoxResult
    result = MsgBox("确定要清除所有输入数据吗？" & vbCrLf & vbCrLf & _
                    "将清除：" & vbCrLf & _
                    "- 功能区编号（第1行）" & vbCrLf & _
                    "- 功能区名、参数（第2-10行）" & vbCrLf & _
                    "- 干支流信息（第11行及以下）", _
                    vbYesNo + vbQuestion, "确认清除")
    
    If result <> vbYes Then Exit Sub
    
    Application.ScreenUpdating = False
    
    ' 获取数据范围
    Dim lastCol As Long, lastRow As Long
    lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    lastRow = ws.Cells(ws.Rows.Count, 4).End(xlUp).Row
    
    If lastCol < 5 Then lastCol = 5
    If lastRow < ROW_MAIN_NAME Then lastRow = ROW_MAIN_NAME
    
    ' 清除 E 列起的内容和背景色
    ws.Range(ws.Cells(1, 5), ws.Cells(lastRow + 20, lastCol)).ClearContents
    ws.Range(ws.Cells(1, 5), ws.Cells(lastRow + 20, lastCol)).Interior.ColorIndex = xlNone
    
    ' 清除 D 列的支流标签（第12行及以下）
    If lastRow >= ROW_BRANCH_START Then
        ws.Range(ws.Cells(ROW_BRANCH_START, 4), ws.Cells(lastRow + 20, 4)).ClearContents
    End If
    
    Application.ScreenUpdating = True
    
    MsgBox "已清除所有输入数据", vbInformation, "完成"
    Exit Sub
    
ErrorHandler:
    Application.ScreenUpdating = True
    MsgBox "出错：" & Err.Description, vbCritical, "错误"
End Sub

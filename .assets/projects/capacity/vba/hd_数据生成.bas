' ============================================================
' 模块名称: Module_数据生成
' 功能描述: 从输入表生成基础信息和逐日流量表
' 创建日期: 2025-01-19
' 作者: 开发部
' ============================================================

Option Explicit

' 行号常量（与 Module_输入准备 一致）
Private Const ROW_ZONE_COUNT As Long = 1
Private Const ROW_SCHEME_COUNT As Long = 2
Private Const ROW_CS As Long = 3
Private Const ROW_K As Long = 4
Private Const ROW_B As Long = 5
Private Const ROW_A As Long = 6
Private Const ROW_BETA As Long = 7
Private Const ROW_MAIN_LENGTH As Long = 8
Private Const ROW_MAIN_C0 As Long = 9
Private Const ROW_BRANCH_COUNT As Long = 10
Private Const ROW_MAIN_NAME As Long = 11
Private Const ROW_BRANCH_START As Long = 12
Private Const ROWS_PER_BRANCH As Long = 5

' ============================================================
' 生成基础信息 - 按钮
' ============================================================
Public Sub 生成基础信息()
    On Error GoTo ErrorHandler
    
    Dim wsInput As Worksheet
    Dim wsOutput As Worksheet
    Dim originalSheet As Worksheet
    
    Set originalSheet = ActiveSheet
    
    ' 获取源 Sheet
    On Error Resume Next
    Set wsInput = ThisWorkbook.Sheets("河道功能区-输入")
    On Error GoTo ErrorHandler
    
    If wsInput Is Nothing Then
        MsgBox "找不到 Sheet「河道功能区-输入」", vbExclamation, "错误"
        Exit Sub
    End If
    
    ' 读取功能区数量
    Dim zoneCount As Long
    zoneCount = SafeLong(wsInput.Cells(ROW_ZONE_COUNT, 2).Value)
    
    If zoneCount <= 0 Then
        MsgBox "请先在 B1 填入功能区数量", vbExclamation, "提示"
        Exit Sub
    End If
    
    Application.ScreenUpdating = False
    
    ' 获取或创建目标 Sheet
    Set wsOutput = GetOrCreateSheet("河道功能区-基础信息", wsInput)
    
    ' 清除旧数据
    wsOutput.Cells.Clear
    
    ' 写入表头
    wsOutput.Cells(1, 1).Value = "功能区"
    wsOutput.Cells(1, 2).Value = "名称"
    wsOutput.Cells(1, 3).Value = "类型"
    wsOutput.Cells(1, 4).Value = "长度L(m)"
    wsOutput.Cells(1, 5).Value = "汇入位置(m)"
    wsOutput.Cells(1, 6).Value = "Cs"
    wsOutput.Cells(1, 7).Value = "C0"
    wsOutput.Cells(1, 8).Value = "K(1/s)"
    wsOutput.Cells(1, 9).Value = "b"
    wsOutput.Cells(1, 10).Value = "a"
    wsOutput.Cells(1, 11).Value = "β"
    wsOutput.Range("A1:K1").Interior.Color = COLOR_AUTO
    
    ' 生成数据行
    Dim outRow As Long
    Dim i As Long, j As Long, col As Long, baseRow As Long
    Dim zoneName As String, streamName As String
    Dim Cs As Double, K As Double, b As Double, a As Double, beta As Double
    Dim mainLength As Double, mainC0 As Double
    Dim branchCount As Long
    Dim branchLength As Double, branchPos As Double, branchC0 As Double
    
    outRow = 2
    
    For i = 1 To zoneCount
        col = 4 + i
        
        ' 读取功能区参数
        zoneName = SafeString(wsInput.Cells(ROW_SCHEME_COUNT, col).Value)
        If Len(zoneName) = 0 Then GoTo NextZone
        
        Cs = SafeDouble(wsInput.Cells(ROW_CS, col).Value)
        K = SafeDouble(wsInput.Cells(ROW_K, col).Value)
        b = SafeDouble(wsInput.Cells(ROW_B, col).Value)
        a = SafeDouble(wsInput.Cells(ROW_A, col).Value)
        beta = SafeDouble(wsInput.Cells(ROW_BETA, col).Value)
        mainLength = SafeDouble(wsInput.Cells(ROW_MAIN_LENGTH, col).Value)
        mainC0 = SafeDouble(wsInput.Cells(ROW_MAIN_C0, col).Value)
        branchCount = SafeLong(wsInput.Cells(ROW_BRANCH_COUNT, col).Value)
        
        ' 写入干流
        streamName = zoneName & "-0"
        wsOutput.Cells(outRow, 1).Value = zoneName
        wsOutput.Cells(outRow, 2).Value = streamName
        wsOutput.Cells(outRow, 3).Value = "干流"
        wsOutput.Cells(outRow, 4).Value = mainLength
        wsOutput.Cells(outRow, 5).Value = ""  ' 干流无汇入位置
        wsOutput.Cells(outRow, 6).Value = Cs
        wsOutput.Cells(outRow, 7).Value = mainC0
        wsOutput.Cells(outRow, 8).Value = K
        wsOutput.Cells(outRow, 9).Value = b
        wsOutput.Cells(outRow, 10).Value = a
        wsOutput.Cells(outRow, 11).Value = beta
        outRow = outRow + 1
        
        ' 写入支流
        For j = 1 To branchCount
            baseRow = ROW_BRANCH_START + (j - 1) * ROWS_PER_BRANCH
            
            streamName = SafeString(wsInput.Cells(baseRow + 1, col).Value)
            If Len(streamName) = 0 Then streamName = zoneName & "-" & j
            
            branchLength = SafeDouble(wsInput.Cells(baseRow + 2, col).Value)
            branchPos = SafeDouble(wsInput.Cells(baseRow + 3, col).Value)
            branchC0 = SafeDouble(wsInput.Cells(baseRow + 4, col).Value)
            
            wsOutput.Cells(outRow, 1).Value = zoneName
            wsOutput.Cells(outRow, 2).Value = streamName
            wsOutput.Cells(outRow, 3).Value = "支流"
            wsOutput.Cells(outRow, 4).Value = branchLength
            wsOutput.Cells(outRow, 5).Value = branchPos
            wsOutput.Cells(outRow, 6).Value = Cs
            wsOutput.Cells(outRow, 7).Value = branchC0
            wsOutput.Cells(outRow, 8).Value = K
            wsOutput.Cells(outRow, 9).Value = b
            wsOutput.Cells(outRow, 10).Value = a
            wsOutput.Cells(outRow, 11).Value = beta
            outRow = outRow + 1
        Next j
        
NextZone:
    Next i
    
    ' 设置数据区背景色
    If outRow > 2 Then
        wsOutput.Range(wsOutput.Cells(2, 1), wsOutput.Cells(outRow - 1, 11)).Interior.Color = COLOR_AUTO
    End If
    
    ' 恢复原 Sheet
    originalSheet.Activate
    
    Application.ScreenUpdating = True
    
    MsgBox "基础信息生成完成！" & vbCrLf & vbCrLf & _
           "共生成 " & (outRow - 2) & " 行数据" & vbCrLf & _
           "请查看「河道功能区-基础信息」Sheet", vbInformation, "完成"
    Exit Sub
    
ErrorHandler:
    Application.ScreenUpdating = True
    MsgBox "出错：" & Err.Description, vbCritical, "错误"
End Sub

' ============================================================
' 生成逐日流量 - 按钮
' ============================================================
Public Sub 生成逐日流量()
    On Error GoTo ErrorHandler
    
    Dim wsInput As Worksheet
    Dim originalSheet As Worksheet
    
    Set originalSheet = ActiveSheet
    
    ' 获取源 Sheet
    On Error Resume Next
    Set wsInput = ThisWorkbook.Sheets("河道功能区-输入")
    On Error GoTo ErrorHandler
    
    If wsInput Is Nothing Then
        MsgBox "找不到 Sheet「河道功能区-输入」", vbExclamation, "错误"
        Exit Sub
    End If
    
    ' 读取功能区数量和方案数
    Dim zoneCount As Long, schemeCount As Long
    zoneCount = SafeLong(wsInput.Cells(ROW_ZONE_COUNT, 2).Value)
    schemeCount = SafeLong(wsInput.Cells(ROW_SCHEME_COUNT, 2).Value)
    
    If zoneCount <= 0 Then
        MsgBox "请先在 B1 填入功能区数量", vbExclamation, "提示"
        Exit Sub
    End If
    
    If schemeCount <= 0 Then
        MsgBox "请先在 B2 填入计算方案个数", vbExclamation, "提示"
        Exit Sub
    End If
    
    Application.ScreenUpdating = False
    
    ' 收集所有干支流名称
    Dim streamNames() As String
    Dim streamCount As Long
    Dim i As Long, j As Long, col As Long, baseRow As Long
    Dim zoneName As String
    Dim branchCount As Long
    
    ' 先统计总数
    streamCount = 0
    For i = 1 To zoneCount
        col = 4 + i
        zoneName = SafeString(wsInput.Cells(ROW_SCHEME_COUNT, col).Value)
        branchCount = SafeLong(wsInput.Cells(ROW_BRANCH_COUNT, col).Value)
        If Len(zoneName) > 0 Then
            streamCount = streamCount + 1 + branchCount
        End If
    Next i
    
    If streamCount = 0 Then
        Application.ScreenUpdating = True
        MsgBox "没有找到功能区，请先填写功能区名", vbExclamation, "提示"
        Exit Sub
    End If
    
    ' 收集名称
    ReDim streamNames(1 To streamCount)
    Dim idx As Long
    idx = 1
    
    For i = 1 To zoneCount
        col = 4 + i
        zoneName = SafeString(wsInput.Cells(ROW_SCHEME_COUNT, col).Value)
        branchCount = SafeLong(wsInput.Cells(ROW_BRANCH_COUNT, col).Value)
        
        If Len(zoneName) > 0 Then
            ' 干流
            streamNames(idx) = zoneName & "-0"
            idx = idx + 1
            
            ' 支流
            For j = 1 To branchCount
                streamNames(idx) = zoneName & "-" & j
                idx = idx + 1
            Next j
        End If
    Next i
    
    ' 生成每个方案的 Sheet
    Dim wsScheme As Worksheet
    Dim sheetName As String
    Dim k As Long
    
    For k = 1 To schemeCount
        sheetName = "逐日流量（方案" & k & "）"
        Set wsScheme = GetOrCreateSheet(sheetName)
        wsScheme.Cells.Clear
        
        ' 写入表头
        wsScheme.Cells(1, 1).Value = "日期"
        wsScheme.Cells(1, 1).Interior.Color = COLOR_AUTO
        
        For idx = 1 To streamCount
            wsScheme.Cells(1, idx + 1).Value = streamNames(idx)
            wsScheme.Cells(1, idx + 1).Interior.Color = COLOR_AUTO
        Next idx
    Next k
    
    ' 恢复原 Sheet
    originalSheet.Activate
    
    Application.ScreenUpdating = True
    
    MsgBox "逐日流量 Sheet 生成完成！" & vbCrLf & vbCrLf & _
           "共生成 " & schemeCount & " 个方案 Sheet" & vbCrLf & _
           "每个 Sheet 有 " & streamCount & " 个干支流列" & vbCrLf & vbCrLf & _
           "请在各方案 Sheet 中填入逐日流量数据", vbInformation, "完成"
    Exit Sub
    
ErrorHandler:
    Application.ScreenUpdating = True
    MsgBox "出错：" & Err.Description, vbCritical, "错误"
End Sub

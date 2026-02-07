' ============================================================
' 模块名称: sk_数据生成
' 功能描述: 水库纳污能力计算 - 基础信息和逐日库容表生成
' 创建日期: 2025-01-20
' 作者: 开发部
' ============================================================

Option Explicit

' 行号常量（与 sk_输入准备 一致）
Private Const ROW_ZONE_COUNT As Long = 1
Private Const ROW_SCHEME_COUNT As Long = 2
Private Const ROW_CS As Long = 3
Private Const ROW_K As Long = 4
Private Const ROW_B As Long = 5

' ============================================================
' 生成基础信息 - 按钮3
' ============================================================
Public Sub SK_生成基础信息()
    On Error GoTo ErrorHandler
    
    Dim wsInput As Worksheet
    Dim wsOutput As Worksheet
    Dim originalSheet As Worksheet
    
    Set originalSheet = ActiveSheet
    
    ' 获取源 Sheet
    On Error Resume Next
    Set wsInput = ThisWorkbook.Sheets("水库功能区-输入")
    On Error GoTo ErrorHandler
    
    If wsInput Is Nothing Then
        MsgBox "找不到 Sheet「水库功能区-输入」", vbExclamation, "错误"
        Exit Sub
    End If
    
    ' 读取功能区数量
    Dim zoneCount As Long
    zoneCount = SK_SafeLong(wsInput.Cells(ROW_ZONE_COUNT, 2).Value)
    
    If zoneCount <= 0 Then
        MsgBox "请先在 B1 填入功能区数量", vbExclamation, "提示"
        Exit Sub
    End If
    
    Application.ScreenUpdating = False
    
    ' 获取或创建目标 Sheet
    Set wsOutput = SK_GetOrCreateSheet("水库功能区-基础信息", wsInput)
    
    ' 清除旧数据
    wsOutput.Cells.Clear
    
    ' 写入表头
    wsOutput.Cells(1, 1).Value = "功能区"
    wsOutput.Cells(1, 2).Value = "名称"
    wsOutput.Cells(1, 3).Value = "Cs"
    wsOutput.Cells(1, 4).Value = "K(1/s)"
    wsOutput.Cells(1, 5).Value = "b"
    wsOutput.Range("A1:E1").Interior.Color = SK_COLOR_AUTO
    wsOutput.Range("A1:E1").Font.Bold = True
    
    ' 设置列宽
    wsOutput.Columns("A").ColumnWidth = 12
    wsOutput.Columns("B").ColumnWidth = 16
    wsOutput.Columns("C").ColumnWidth = 10
    wsOutput.Columns("D").ColumnWidth = 12
    wsOutput.Columns("E").ColumnWidth = 10
    
    ' 生成数据行
    Dim outRow As Long
    Dim i As Long, col As Long
    Dim zoneName As String
    Dim Cs As Double, K As Double, b As Double
    
    outRow = 2
    
    For i = 1 To zoneCount
        col = 4 + i
        
        ' 读取功能区参数
        zoneName = SK_SafeString(wsInput.Cells(ROW_SCHEME_COUNT, col).Value)
        If Len(zoneName) = 0 Then GoTo NextZone
        
        Cs = SK_SafeDouble(wsInput.Cells(ROW_CS, col).Value)
        K = SK_SafeDouble(wsInput.Cells(ROW_K, col).Value)
        b = SK_SafeDouble(wsInput.Cells(ROW_B, col).Value)
        
        ' 写入行
        wsOutput.Cells(outRow, 1).Value = "SK-" & Format(i, "00")
        wsOutput.Cells(outRow, 2).Value = zoneName
        wsOutput.Cells(outRow, 3).Value = Cs
        wsOutput.Cells(outRow, 4).Value = K
        wsOutput.Cells(outRow, 5).Value = b
        
        outRow = outRow + 1
        
NextZone:
    Next i
    
    ' 设置数据区背景色
    If outRow > 2 Then
        wsOutput.Range(wsOutput.Cells(2, 1), wsOutput.Cells(outRow - 1, 5)).Interior.Color = SK_COLOR_AUTO
    End If
    
    ' 恢复原 Sheet
    originalSheet.Activate
    
    Application.ScreenUpdating = True
    
    MsgBox "基础信息生成完成！" & vbCrLf & vbCrLf & _
           "共生成 " & (outRow - 2) & " 个功能区" & vbCrLf & _
           "请查看「水库功能区-基础信息」Sheet" & vbCrLf & vbCrLf & _
           "然后点击「生成逐日库容」", vbInformation, "完成"
    Exit Sub
    
ErrorHandler:
    Application.ScreenUpdating = True
    MsgBox "出错：" & Err.Description, vbCritical, "错误"
End Sub

' ============================================================
' 生成逐日库容 - 按钮4
' ============================================================
Public Sub SK_生成逐日库容()
    On Error GoTo ErrorHandler
    
    Dim wsInput As Worksheet
    Dim wsInfo As Worksheet
    Dim originalSheet As Worksheet
    
    Set originalSheet = ActiveSheet
    
    ' 获取源 Sheet
    On Error Resume Next
    Set wsInput = ThisWorkbook.Sheets("水库功能区-输入")
    Set wsInfo = ThisWorkbook.Sheets("水库功能区-基础信息")
    On Error GoTo ErrorHandler
    
    If wsInput Is Nothing Then
        MsgBox "找不到 Sheet「水库功能区-输入」", vbExclamation, "错误"
        Exit Sub
    End If
    
    If wsInfo Is Nothing Then
        MsgBox "找不到 Sheet「水库功能区-基础信息」" & vbCrLf & _
               "请先点击「生成基础信息」按钮", vbExclamation, "错误"
        Exit Sub
    End If
    
    ' 读取方案数
    Dim schemeCount As Long
    schemeCount = SK_SafeLong(wsInput.Cells(ROW_SCHEME_COUNT, 2).Value)
    
    If schemeCount <= 0 Then
        MsgBox "请先在 B2 填入计算方案个数", vbExclamation, "提示"
        Exit Sub
    End If
    
    Application.ScreenUpdating = False
    
    ' 读取功能区名称
    Dim lastRow As Long
    lastRow = SK_GetLastRow(wsInfo, 1)
    
    If lastRow <= 1 Then
        Application.ScreenUpdating = True
        MsgBox "基础信息表没有数据", vbExclamation, "提示"
        Exit Sub
    End If
    
    Dim zoneNames() As String
    Dim zoneCount As Long
    zoneCount = lastRow - 1
    ReDim zoneNames(1 To zoneCount)
    
    Dim i As Long
    For i = 1 To zoneCount
        zoneNames(i) = SK_SafeString(wsInfo.Cells(i + 1, 2).Value)
    Next i
    
    ' 生成每个方案的 Sheet
    Dim wsScheme As Worksheet
    Dim sheetName As String
    Dim k As Long
    
    For k = 1 To schemeCount
        sheetName = "水库逐日库容（方案" & k & "）"
        Set wsScheme = SK_GetOrCreateSheet(sheetName)
        wsScheme.Cells.Clear
        
        ' 写入表头
        wsScheme.Cells(1, 1).Value = "日期"
        wsScheme.Cells(1, 1).Interior.Color = SK_COLOR_AUTO
        wsScheme.Columns("A").ColumnWidth = 12
        
        For i = 1 To zoneCount
            wsScheme.Cells(1, i + 1).Value = zoneNames(i)
            wsScheme.Cells(1, i + 1).Interior.Color = SK_COLOR_AUTO
            wsScheme.Columns(i + 1).ColumnWidth = 14
        Next i
        
        wsScheme.Range("A1").Font.Bold = True
        wsScheme.Range(wsScheme.Cells(1, 1), wsScheme.Cells(1, zoneCount + 1)).Font.Bold = True
    Next k
    
    ' 恢复原 Sheet
    originalSheet.Activate
    
    Application.ScreenUpdating = True
    
    MsgBox "逐日库容 Sheet 生成完成！" & vbCrLf & vbCrLf & _
           "共生成 " & schemeCount & " 个方案 Sheet" & vbCrLf & _
           "每个 Sheet 有 " & zoneCount & " 个功能区列" & vbCrLf & vbCrLf & _
           "请在各方案 Sheet 中填入：" & vbCrLf & _
           "- A列：日期（如 2020-04-01）" & vbCrLf & _
           "- B列起：各功能区逐日库容(m³)" & vbCrLf & vbCrLf & _
           "填好后点击「开始计算」", vbInformation, "完成"
    Exit Sub
    
ErrorHandler:
    Application.ScreenUpdating = True
    MsgBox "出错：" & Err.Description, vbCritical, "错误"
End Sub

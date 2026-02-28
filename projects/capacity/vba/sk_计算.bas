' ============================================================
' 模块名称: sk_计算
' 功能描述: 水库纳污能力核心计算
' 创建日期: 2025-01-20
' 作者: 开发部
' ============================================================
'
' 水库纳污能力公式:
'   W = 31.536 × K × V × Cs × b
'
' 其中：
'   W：纳污能力 (t/a)
'   K：污染物综合衰减系数 (1/s)
'   V：库容 (m³)
'   Cs：目标浓度 (mg/L)
'   b：不均匀系数
'
' 时间尺度：水文年（4月→次年3月）
' ============================================================

Option Explicit

' 功能区信息结构
Private Type SK_ZoneInfo
    ZoneID As String        ' 功能区编号
    Name As String          ' 功能区名
    Cs As Double
    K As Double
    b As Double
End Type

' ============================================================
' 开始计算 - 按钮5
' ============================================================
Public Sub SK_开始计算()
    On Error GoTo ErrorHandler
    
    Dim originalSheet As Worksheet
    Set originalSheet = ActiveSheet
    
    ' 检查必要的 Sheet
    If Not SK_SheetExists("水库功能区-输入") Then
        MsgBox "找不到「水库功能区-输入」Sheet", vbExclamation, "提示"
        Exit Sub
    End If
    
    If Not SK_SheetExists("水库功能区-基础信息") Then
        MsgBox "找不到「水库功能区-基础信息」Sheet" & vbCrLf & _
               "请先点击「生成基础信息」按钮", vbExclamation, "提示"
        Exit Sub
    End If
    
    Dim wsInput As Worksheet
    Set wsInput = ThisWorkbook.Sheets("水库功能区-输入")
    
    ' 获取方案数量
    Dim schemeCount As Long
    schemeCount = SK_SafeLong(wsInput.Cells(2, 2).Value)
    
    If schemeCount <= 0 Then
        MsgBox "请先在 B2 填入计算方案个数", vbExclamation, "提示"
        Exit Sub
    End If
    
    ' 检查逐日库容 Sheet
    Dim k As Long
    For k = 1 To schemeCount
        If Not SK_SheetExists("水库逐日库容（方案" & k & "）") Then
            MsgBox "找不到「水库逐日库容（方案" & k & "）」Sheet" & vbCrLf & _
                   "请先点击「生成逐日库容」按钮", vbExclamation, "提示"
            Exit Sub
        End If
    Next k
    
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    
    ' 读取功能区信息
    Dim zones() As SK_ZoneInfo
    Dim zoneCount As Long
    Call ReadZoneInfo(zones, zoneCount)
    
    If zoneCount = 0 Then
        Application.Calculation = xlCalculationAutomatic
        Application.ScreenUpdating = True
        MsgBox "没有找到功能区数据", vbExclamation, "提示"
        Exit Sub
    End If
    
    ' 对每个方案进行计算
    For k = 1 To schemeCount
        Call CalculateScheme(k, zones, zoneCount)
    Next k
    
    ' 恢复原 Sheet
    originalSheet.Activate
    
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    
    MsgBox "计算完成！" & vbCrLf & vbCrLf & _
           "已生成 " & schemeCount & " 个方案的计算结果" & vbCrLf & _
           "请查看「水库纳污能力（方案N）」Sheet" & vbCrLf & vbCrLf & _
           "注：按水文年顺序（4月→3月）", vbInformation, "完成"
    Exit Sub
    
ErrorHandler:
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    MsgBox "计算出错：" & Err.Description, vbCritical, "错误"
End Sub

' ============================================================
' 读取功能区信息
' ============================================================
Private Sub ReadZoneInfo(ByRef zones() As SK_ZoneInfo, ByRef zoneCount As Long)
    Dim wsInfo As Worksheet
    Set wsInfo = ThisWorkbook.Sheets("水库功能区-基础信息")
    
    Dim lastRow As Long
    lastRow = SK_GetLastRow(wsInfo, 1)
    
    If lastRow <= 1 Then
        zoneCount = 0
        Exit Sub
    End If
    
    zoneCount = lastRow - 1
    ReDim zones(1 To zoneCount)
    
    Dim i As Long
    For i = 1 To zoneCount
        zones(i).ZoneID = SK_SafeString(wsInfo.Cells(i + 1, 1).Value)
        zones(i).Name = SK_SafeString(wsInfo.Cells(i + 1, 2).Value)
        zones(i).Cs = SK_SafeDouble(wsInfo.Cells(i + 1, 3).Value)
        zones(i).K = SK_SafeDouble(wsInfo.Cells(i + 1, 4).Value)
        zones(i).b = SK_SafeDouble(wsInfo.Cells(i + 1, 5).Value)
    Next i
End Sub

' ============================================================
' 计算单个方案
' ============================================================
Private Sub CalculateScheme(schemeNum As Long, zones() As SK_ZoneInfo, zoneCount As Long)
    Dim wsDaily As Worksheet
    Dim wsResult As Worksheet
    
    Dim schemeSuffix As String
    schemeSuffix = "（方案" & schemeNum & "）"
    
    Set wsDaily = ThisWorkbook.Sheets("水库逐日库容" & schemeSuffix)
    
    ' 读取逐日库容数据
    Dim lastRow As Long, lastCol As Long
    lastRow = SK_GetLastRow(wsDaily, 1)
    lastCol = SK_GetLastCol(wsDaily, 1)
    
    If lastRow <= 1 Then Exit Sub
    
    ' 读取列名（功能区名称）
    Dim colNames() As String
    Dim colCount As Long
    colCount = lastCol - 1
    
    If colCount <= 0 Then Exit Sub
    
    ReDim colNames(1 To colCount)
    
    Dim c As Long
    For c = 1 To colCount
        colNames(c) = SK_SafeString(wsDaily.Cells(1, c + 1).Value)
    Next c
    
    ' 确定水文年范围
    Dim minHydroYear As Long, maxHydroYear As Long
    Dim dateVal As Date
    Dim r As Long
    Dim hydroYear As Long
    
    On Error Resume Next
    dateVal = wsDaily.Cells(2, 1).Value
    On Error GoTo 0
    
    minHydroYear = SK_GetHydroYear(dateVal)
    maxHydroYear = minHydroYear
    
    For r = 2 To lastRow
        On Error Resume Next
        dateVal = wsDaily.Cells(r, 1).Value
        On Error GoTo 0
        hydroYear = SK_GetHydroYear(dateVal)
        If hydroYear < minHydroYear Then minHydroYear = hydroYear
        If hydroYear > maxHydroYear Then maxHydroYear = hydroYear
    Next r
    
    Dim yearCount As Long
    yearCount = maxHydroYear - minHydroYear + 1
    If yearCount <= 0 Then yearCount = 1
    
    ' 创建月度库容汇总数组 (zoneIdx, yearIdx, hydroMonthIdx)
    ' hydroMonthIdx: 1=4月, 2=5月, ..., 9=12月, 10=1月, 11=2月, 12=3月
    Dim monthlyVolumeSum() As Double
    Dim monthlyVolumeCnt() As Long
    ReDim monthlyVolumeSum(1 To zoneCount, 1 To yearCount, 1 To 12)
    ReDim monthlyVolumeCnt(1 To zoneCount, 1 To yearCount, 1 To 12)
    
    ' 初始化
    Dim z As Long, y As Long, m As Long
    For z = 1 To zoneCount
        For y = 1 To yearCount
            For m = 1 To 12
                monthlyVolumeSum(z, y, m) = 0
                monthlyVolumeCnt(z, y, m) = 0
            Next m
        Next y
    Next z
    
    ' 汇总逐日数据
    Dim yearIdx As Long, hydroMonthIdx As Long
    Dim volumeVal As Double
    Dim zoneColIdx As Long
    
    For r = 2 To lastRow
        On Error Resume Next
        dateVal = wsDaily.Cells(r, 1).Value
        On Error GoTo 0
        
        hydroYear = SK_GetHydroYear(dateVal)
        yearIdx = hydroYear - minHydroYear + 1
        hydroMonthIdx = SK_GetHydroMonthIdx(Month(dateVal))
        
        If yearIdx >= 1 And yearIdx <= yearCount And hydroMonthIdx >= 1 And hydroMonthIdx <= 12 Then
            For c = 1 To colCount
                volumeVal = SK_SafeDouble(wsDaily.Cells(r, c + 1).Value)
                
                ' 找到对应的功能区索引
                zoneColIdx = FindZoneIdx(zones, zoneCount, colNames(c))
                
                If zoneColIdx > 0 Then
                    monthlyVolumeSum(zoneColIdx, yearIdx, hydroMonthIdx) = _
                        monthlyVolumeSum(zoneColIdx, yearIdx, hydroMonthIdx) + volumeVal
                    monthlyVolumeCnt(zoneColIdx, yearIdx, hydroMonthIdx) = _
                        monthlyVolumeCnt(zoneColIdx, yearIdx, hydroMonthIdx) + 1
                End If
            Next c
        End If
    Next r
    
    ' 创建结果 Sheet
    Set wsResult = SK_GetOrCreateSheet("水库纳污能力" & schemeSuffix)
    wsResult.Cells.Clear
    
    ' 写入表头（按水文年顺序：4月→3月）
    wsResult.Cells(1, 1).Value = "功能区"
    wsResult.Cells(1, 2).Value = "名称"
    
    ' 月份列（水文年顺序）
    Dim monthNames(1 To 12) As String
    monthNames(1) = "4月"
    monthNames(2) = "5月"
    monthNames(3) = "6月"
    monthNames(4) = "7月"
    monthNames(5) = "8月"
    monthNames(6) = "9月"
    monthNames(7) = "10月"
    monthNames(8) = "11月"
    monthNames(9) = "12月"
    monthNames(10) = "1月"
    monthNames(11) = "2月"
    monthNames(12) = "3月"
    
    For m = 1 To 12
        wsResult.Cells(1, m + 2).Value = monthNames(m)
    Next m
    wsResult.Cells(1, 15).Value = "年合计(t/a)"
    
    wsResult.Range("A1:O1").Interior.Color = SK_COLOR_AUTO
    wsResult.Range("A1:O1").Font.Bold = True
    
    ' 设置列宽
    wsResult.Columns("A").ColumnWidth = 10
    wsResult.Columns("B").ColumnWidth = 14
    For m = 3 To 15
        wsResult.Columns(m).ColumnWidth = 10
    Next m
    
    ' 计算每个功能区的纳污能力
    Dim outRow As Long
    Dim monthCapacity(1 To 12) As Double
    Dim monthCnt(1 To 12) As Long
    Dim yearTotal As Double
    Dim avgVolume As Double
    Dim W As Double
    
    outRow = 2
    
    For z = 1 To zoneCount
        ' 初始化月度统计
        For m = 1 To 12
            monthCapacity(m) = 0
            monthCnt(m) = 0
        Next m
        
        ' 对每个水文年-月计算
        For y = 1 To yearCount
            For m = 1 To 12
                If monthlyVolumeCnt(z, y, m) > 0 Then
                    ' 月平均库容
                    avgVolume = monthlyVolumeSum(z, y, m) / monthlyVolumeCnt(z, y, m)
                    
                    ' 计算纳污能力: W = 31.536 × K × V × Cs × b
                    W = SK_UNIT_FACTOR * zones(z).K * avgVolume * zones(z).Cs * zones(z).b
                    
                    monthCapacity(m) = monthCapacity(m) + W
                    monthCnt(m) = monthCnt(m) + 1
                End If
            Next m
        Next y
        
        ' 写入结果
        wsResult.Cells(outRow, 1).Value = zones(z).ZoneID
        wsResult.Cells(outRow, 2).Value = zones(z).Name
        
        yearTotal = 0
        For m = 1 To 12
            If monthCnt(m) > 0 Then
                wsResult.Cells(outRow, m + 2).Value = Round(monthCapacity(m) / monthCnt(m), 2)
                yearTotal = yearTotal + monthCapacity(m) / monthCnt(m)
            Else
                wsResult.Cells(outRow, m + 2).Value = 0
            End If
        Next m
        wsResult.Cells(outRow, 15).Value = Round(yearTotal, 2)
        
        outRow = outRow + 1
    Next z
    
    ' 设置数据区背景色
    If outRow > 2 Then
        wsResult.Range(wsResult.Cells(2, 1), wsResult.Cells(outRow - 1, 15)).Interior.Color = SK_COLOR_AUTO
    End If
    
    ' 年合计列加粗
    wsResult.Range(wsResult.Cells(1, 15), wsResult.Cells(outRow - 1, 15)).Font.Bold = True
End Sub

' ============================================================
' 根据名称查找功能区索引
' ============================================================
Private Function FindZoneIdx(zones() As SK_ZoneInfo, zoneCount As Long, targetName As String) As Long
    Dim i As Long
    FindZoneIdx = 0
    For i = 1 To zoneCount
        If zones(i).Name = targetName Then
            FindZoneIdx = i
            Exit Function
        End If
    Next i
End Function

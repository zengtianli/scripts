' ============================================================
' 模块名称: Module_计算
' 功能描述: 河道纳污能力核心计算（分段详细输出版）
' 创建日期: 2025-01-19
' 更新日期: 2025-01-19
' 作者: 开发部
' ============================================================
'
' 河道纳污能力公式:
'   W = 31.536 × b × (Cs - C0 × exp(-KL/u)) × (Q×K×L/u) / (1 - exp(-KL/u))
'
' 流速公式:
'   u = a × Q^β
'
' 出流浓度:
'   C_out = C0 × exp(-K×L/u)
'
' 流量混合:
'   Q_mix = Q1 + Q2
'
' 浓度混合:
'   C_mix = (Q1×C1 + Q2×C2) / (Q1 + Q2)
'
' 汇总规则:
'   只汇总干流段的纳污能力，支流和混合点仅展示
' ============================================================

Option Explicit

' 支流信息结构
Private Type BranchInfo
    Name As String          ' 支流名称
    Length As Double        ' 支流长度
    JoinPosition As Double  ' 汇入位置（在干流的第几米）
    C0 As Double            ' 入口浓度
    Q As Double             ' 流量（运行时赋值）
End Type

' 功能区信息结构
Private Type ZoneInfo
    Name As String          ' 功能区名
    MainName As String      ' 干流名
    MainLength As Double    ' 干流总长
    MainC0 As Double        ' 干流入口浓度
    MainQ As Double         ' 干流流量（运行时赋值）
    Cs As Double
    K As Double
    b As Double
    a As Double
    beta As Double
    BranchCount As Long
    Branches() As BranchInfo
End Type

' 分段结果结构
Private Type SegmentResult
    Name As String          ' 河段名称
    SegType As String       ' 类型：干流段/支流/混合/汇总
    Length As Double        ' 长度
    Q As Double             ' 流量
    C0 As Double            ' 入口浓度
    C_out As Double         ' 出口浓度
    W As Double             ' 纳污能力
    Remark As String        ' 备注
End Type

' ============================================================
' 开始计算 - 主入口
' ============================================================
Public Sub 开始计算()
    On Error GoTo ErrorHandler
    
    Dim originalSheet As Worksheet
    Set originalSheet = ActiveSheet
    
    ' 检查必要的 Sheet
    If Not SheetExists("河道功能区-输入") Then
        MsgBox "找不到「河道功能区-输入」Sheet", vbExclamation, "提示"
        Exit Sub
    End If
    
    If Not SheetExists("河道功能区-基础信息") Then
        MsgBox "找不到「河道功能区-基础信息」Sheet" & vbCrLf & _
               "请先点击「生成基础信息」按钮", vbExclamation, "提示"
        Exit Sub
    End If
    
    Dim wsInput As Worksheet
    Set wsInput = ThisWorkbook.Sheets("河道功能区-输入")
    
    ' 获取方案数量
    Dim schemeCount As Long
    schemeCount = SafeLong(wsInput.Cells(2, 2).Value)
    
    If schemeCount <= 0 Then
        MsgBox "请先在 B2 填入计算方案个数", vbExclamation, "提示"
        Exit Sub
    End If
    
    ' 检查逐日流量 Sheet
    Dim k As Long
    For k = 1 To schemeCount
        If Not SheetExists("逐日流量（方案" & k & "）") Then
            MsgBox "找不到「逐日流量（方案" & k & "）」Sheet" & vbCrLf & _
                   "请先点击「生成逐日流量」按钮", vbExclamation, "提示"
            Exit Sub
        End If
    Next k
    
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    
    ' 读取功能区信息
    Dim zones() As ZoneInfo
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
           "已生成 " & schemeCount & " 个方案的详细计算结果" & vbCrLf & _
           "请查看「纳污能力（方案N）」Sheet", vbInformation, "完成"
    Exit Sub
    
ErrorHandler:
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    MsgBox "计算出错：" & Err.Description, vbCritical, "错误"
End Sub

' ============================================================
' 读取功能区信息
' ============================================================
Private Sub ReadZoneInfo(ByRef zones() As ZoneInfo, ByRef zoneCount As Long)
    Dim wsInfo As Worksheet
    Set wsInfo = ThisWorkbook.Sheets("河道功能区-基础信息")
    
    Dim lastRow As Long
    lastRow = GetLastRow(wsInfo, 1)
    
    If lastRow <= 1 Then
        zoneCount = 0
        Exit Sub
    End If
    
    ' 先统计功能区数量（干流数）
    Dim i As Long
    zoneCount = 0
    For i = 2 To lastRow
        If SafeString(wsInfo.Cells(i, 3).Value) = "干流" Then
            zoneCount = zoneCount + 1
        End If
    Next i
    
    If zoneCount = 0 Then Exit Sub
    
    ReDim zones(1 To zoneCount)
    
    ' 读取数据
    Dim zIdx As Long, bIdx As Long
    Dim streamType As String
    
    zIdx = 0
    
    For i = 2 To lastRow
        streamType = SafeString(wsInfo.Cells(i, 3).Value)
        
        If streamType = "干流" Then
            ' 新功能区
            zIdx = zIdx + 1
            zones(zIdx).Name = SafeString(wsInfo.Cells(i, 1).Value)
            zones(zIdx).MainName = SafeString(wsInfo.Cells(i, 2).Value)
            zones(zIdx).MainLength = SafeDouble(wsInfo.Cells(i, 4).Value)
            zones(zIdx).MainC0 = SafeDouble(wsInfo.Cells(i, 7).Value)
            zones(zIdx).Cs = SafeDouble(wsInfo.Cells(i, 6).Value)
            zones(zIdx).K = SafeDouble(wsInfo.Cells(i, 8).Value)
            zones(zIdx).b = SafeDouble(wsInfo.Cells(i, 9).Value)
            zones(zIdx).a = SafeDouble(wsInfo.Cells(i, 10).Value)
            zones(zIdx).beta = SafeDouble(wsInfo.Cells(i, 11).Value)
            zones(zIdx).BranchCount = 0
            ReDim zones(zIdx).Branches(1 To 10)  ' 预分配最多10条支流
            
        ElseIf streamType = "支流" And zIdx > 0 Then
            ' 支流（属于当前功能区）
            zones(zIdx).BranchCount = zones(zIdx).BranchCount + 1
            bIdx = zones(zIdx).BranchCount
            
            If bIdx <= 10 Then
                zones(zIdx).Branches(bIdx).Name = SafeString(wsInfo.Cells(i, 2).Value)
                zones(zIdx).Branches(bIdx).Length = SafeDouble(wsInfo.Cells(i, 4).Value)
                zones(zIdx).Branches(bIdx).JoinPosition = SafeDouble(wsInfo.Cells(i, 5).Value)
                zones(zIdx).Branches(bIdx).C0 = SafeDouble(wsInfo.Cells(i, 7).Value)
            End If
        End If
    Next i
End Sub

' ============================================================
' 计算单个方案（详细输出版 + 逐日逐月）
' ============================================================
Private Sub CalculateScheme(schemeNum As Long, zones() As ZoneInfo, zoneCount As Long)
    Dim wsDaily As Worksheet
    Dim wsResult As Worksheet
    
    Dim schemeSuffix As String
    schemeSuffix = "（方案" & schemeNum & "）"
    
    Set wsDaily = ThisWorkbook.Sheets("逐日流量" & schemeSuffix)
    
    ' 读取逐日流量数据
    Dim lastRow As Long, lastCol As Long
    lastRow = GetLastRow(wsDaily, 1)
    lastCol = GetLastCol(wsDaily, 1)
    
    If lastRow <= 1 Then Exit Sub
    
    Dim streamCount As Long
    streamCount = lastCol - 1
    
    If streamCount <= 0 Then Exit Sub
    
    ' 读取列名
    Dim colNames() As String
    ReDim colNames(1 To streamCount)
    
    Dim c As Long
    For c = 1 To streamCount
        colNames(c) = SafeString(wsDaily.Cells(1, c + 1).Value)
    Next c
    
    ' 确定年份范围
    Dim minYear As Long, maxYear As Long
    Dim dateVal As Date
    Dim r As Long
    
    On Error Resume Next
    dateVal = wsDaily.Cells(2, 1).Value
    On Error GoTo 0
    
    minYear = Year(dateVal)
    maxYear = Year(dateVal)
    
    For r = 2 To lastRow
        On Error Resume Next
        dateVal = wsDaily.Cells(r, 1).Value
        On Error GoTo 0
        If Year(dateVal) < minYear Then minYear = Year(dateVal)
        If Year(dateVal) > maxYear Then maxYear = Year(dateVal)
    Next r
    
    Dim yearCount As Long
    yearCount = maxYear - minYear + 1
    If yearCount <= 0 Then yearCount = 1
    
    ' ========== 创建逐日纳污能力 Sheet ==========
    Dim wsDailyW As Worksheet
    Set wsDailyW = GetOrCreateSheet("逐日纳污能力" & schemeSuffix)
    wsDailyW.Cells.Clear
    
    ' 逐日表头
    wsDailyW.Cells(1, 1).Value = "日期"
    wsDailyW.Cells(1, 1).Interior.Color = COLOR_AUTO
    wsDailyW.Columns("A").ColumnWidth = 12
    
    Dim i As Long
    For i = 1 To zoneCount
        wsDailyW.Cells(1, i + 1).Value = zones(i).Name
        wsDailyW.Cells(1, i + 1).Interior.Color = COLOR_AUTO
        wsDailyW.Columns(i + 1).ColumnWidth = 12
    Next i
    wsDailyW.Range("A1").Font.Bold = True
    wsDailyW.Range(wsDailyW.Cells(1, 1), wsDailyW.Cells(1, zoneCount + 1)).Font.Bold = True
    
    ' ========== 创建逐月纳污能力 Sheet ==========
    Dim wsMonthlyW As Worksheet
    Set wsMonthlyW = GetOrCreateSheet("逐月纳污能力" & schemeSuffix)
    wsMonthlyW.Cells.Clear
    
    ' 逐月表头
    wsMonthlyW.Cells(1, 1).Value = "月份"
    wsMonthlyW.Cells(1, 1).Interior.Color = COLOR_AUTO
    wsMonthlyW.Columns("A").ColumnWidth = 10
    
    For i = 1 To zoneCount
        wsMonthlyW.Cells(1, i + 1).Value = zones(i).Name
        wsMonthlyW.Cells(1, i + 1).Interior.Color = COLOR_AUTO
        wsMonthlyW.Columns(i + 1).ColumnWidth = 12
    Next i
    wsMonthlyW.Cells(1, zoneCount + 2).Value = "合计"
    wsMonthlyW.Cells(1, zoneCount + 2).Interior.Color = COLOR_AUTO
    wsMonthlyW.Range("A1").Font.Bold = True
    wsMonthlyW.Range(wsMonthlyW.Cells(1, 1), wsMonthlyW.Cells(1, zoneCount + 2)).Font.Bold = True
    
    ' 创建月度纳污能力汇总数组（功能区级别）
    Dim monthlyWSum() As Double
    Dim monthlyWCnt() As Long
    ReDim monthlyWSum(1 To zoneCount, 1 To 12)
    ReDim monthlyWCnt(1 To zoneCount, 1 To 12)
    
    ' ========== 新增：分段汇总数组（逐日逐段为最小单位） ==========
    ' 最大段数 = 支流数×2 + 3（首尾干流段+汇总）
    Const MAX_SEGS As Long = 25
    
    ' 分段累计数组：segWSum(zone, seg) = 该段所有天的W累计
    Dim segWSum() As Double
    Dim segWCnt() As Long
    ReDim segWSum(1 To zoneCount, 1 To MAX_SEGS)
    ReDim segWCnt(1 To zoneCount, 1 To MAX_SEGS)
    
    ' 分段信息数组（首次计算时记录）
    Dim segInfoName() As String
    Dim segInfoType() As String
    Dim segInfoLength() As Double
    Dim segInfoRemark() As String
    Dim zoneSegCount() As Long
    ReDim segInfoName(1 To zoneCount, 1 To MAX_SEGS)
    ReDim segInfoType(1 To zoneCount, 1 To MAX_SEGS)
    ReDim segInfoLength(1 To zoneCount, 1 To MAX_SEGS)
    ReDim segInfoRemark(1 To zoneCount, 1 To MAX_SEGS)
    ReDim zoneSegCount(1 To zoneCount)
    
    ' 分段Q/C累计（用于计算年平均）
    Dim segQSum() As Double
    Dim segC0Sum() As Double
    Dim segCoutSum() As Double
    ReDim segQSum(1 To zoneCount, 1 To MAX_SEGS)
    ReDim segC0Sum(1 To zoneCount, 1 To MAX_SEGS)
    ReDim segCoutSum(1 To zoneCount, 1 To MAX_SEGS)
    
    ' 初始化数组
    Dim s As Long, m As Long
    For i = 1 To zoneCount
        zoneSegCount(i) = 0
        For m = 1 To 12
            monthlyWSum(i, m) = 0
            monthlyWCnt(i, m) = 0
        Next m
        For s = 1 To MAX_SEGS
            segWSum(i, s) = 0
            segWCnt(i, s) = 0
            segQSum(i, s) = 0
            segC0Sum(i, s) = 0
            segCoutSum(i, s) = 0
        Next s
    Next i
    
    Dim segInfoRecorded As Boolean
    segInfoRecorded = False
    
    ' ========== 逐日计算纳污能力（使用逐日逐段为最小单位） ==========
    Dim outRowDaily As Long
    Dim yearIdx As Long, monthVal As Long
    Dim dailyW As Double
    Dim j As Long
    Dim mainColIdx As Long, branchColIdx As Long
    Dim segments() As SegmentResult
    Dim segCount As Long
    Dim seg As Long
    
    outRowDaily = 2
    
    For r = 2 To lastRow
        On Error Resume Next
        dateVal = wsDaily.Cells(r, 1).Value
        On Error GoTo 0
        
        yearIdx = Year(dateVal) - minYear + 1
        monthVal = Month(dateVal)
        
        ' 写入日期
        wsDailyW.Cells(outRowDaily, 1).Value = dateVal
        
        ' 对每个功能区计算当日纳污能力（分段计算）
        For i = 1 To zoneCount
            ' 获取当日干流流量
            mainColIdx = FindColIdx(colNames, streamCount, zones(i).MainName)
            If mainColIdx > 0 Then
                zones(i).MainQ = SafeDouble(wsDaily.Cells(r, mainColIdx + 1).Value)
            Else
                zones(i).MainQ = 0
            End If
            
            ' 获取当日各支流流量
            For j = 1 To zones(i).BranchCount
                branchColIdx = FindColIdx(colNames, streamCount, zones(i).Branches(j).Name)
                If branchColIdx > 0 Then
                    zones(i).Branches(j).Q = SafeDouble(wsDaily.Cells(r, branchColIdx + 1).Value)
                Else
                    zones(i).Branches(j).Q = 0
                End If
            Next j
            
            ' 计算当日分段纳污能力
            dailyW = 0
            If zones(i).MainQ > 0 Then
                Call CalcZoneSegments(zones(i), segments, segCount)
                
                ' 首次记录分段信息
                If Not segInfoRecorded Then
                    zoneSegCount(i) = segCount
                    For seg = 1 To segCount
                        segInfoName(i, seg) = segments(seg).Name
                        segInfoType(i, seg) = segments(seg).SegType
                        segInfoLength(i, seg) = segments(seg).Length
                        segInfoRemark(i, seg) = segments(seg).Remark
                    Next seg
                End If
                
                ' 累加各段结果到分段汇总数组
                For seg = 1 To segCount
                    segWSum(i, seg) = segWSum(i, seg) + segments(seg).W
                    segWCnt(i, seg) = segWCnt(i, seg) + 1
                    segQSum(i, seg) = segQSum(i, seg) + segments(seg).Q
                    segC0Sum(i, seg) = segC0Sum(i, seg) + segments(seg).C0
                    segCoutSum(i, seg) = segCoutSum(i, seg) + segments(seg).C_out
                    
                    ' 只累加干流段到功能区总W
                    If segments(seg).SegType = "干流段" Then
                        dailyW = dailyW + segments(seg).W
                    End If
                Next seg
            End If
            
            ' 写入逐日表（功能区当日总纳污能力 = 各干流段之和）
            wsDailyW.Cells(outRowDaily, i + 1).Value = Round(dailyW, 2)
            
            ' 累加到月度汇总
            If monthVal >= 1 And monthVal <= 12 Then
                monthlyWSum(i, monthVal) = monthlyWSum(i, monthVal) + dailyW
                monthlyWCnt(i, monthVal) = monthlyWCnt(i, monthVal) + 1
            End If
        Next i
        
        ' 首天循环结束后标记分段信息已记录
        If Not segInfoRecorded Then segInfoRecorded = True
        
        outRowDaily = outRowDaily + 1
    Next r
    
    ' 设置逐日表背景色
    wsDailyW.Range(wsDailyW.Cells(2, 1), wsDailyW.Cells(outRowDaily - 1, zoneCount + 1)).Interior.Color = COLOR_AUTO
    
    ' ========== 输出逐月纳污能力 ==========
    Dim outRowMonthly As Long
    Dim monthTotal As Double
    Dim yearTotal() As Double      ' 12个月平均的累加（用于年合计）
    Dim yearWSum() As Double       ' 所有天的总和（用于年平均）
    Dim yearWCnt() As Long         ' 所有天的天数（用于年平均）
    ReDim yearTotal(1 To zoneCount)
    ReDim yearWSum(1 To zoneCount)
    ReDim yearWCnt(1 To zoneCount)
    
    For i = 1 To zoneCount
        yearTotal(i) = 0
        yearWSum(i) = 0
        yearWCnt(i) = 0
    Next i
    
    outRowMonthly = 2
    
    For m = 1 To 12
        wsMonthlyW.Cells(outRowMonthly, 1).Value = m & "月"
        monthTotal = 0
        
        For i = 1 To zoneCount
            If monthlyWCnt(i, m) > 0 Then
                ' 月平均纳污能力
                dailyW = monthlyWSum(i, m) / monthlyWCnt(i, m)
                wsMonthlyW.Cells(outRowMonthly, i + 1).Value = Round(dailyW, 2)
                yearTotal(i) = yearTotal(i) + dailyW
                monthTotal = monthTotal + dailyW
                
                ' 累加到年度总和（用于计算真正的年平均）
                yearWSum(i) = yearWSum(i) + monthlyWSum(i, m)
                yearWCnt(i) = yearWCnt(i) + monthlyWCnt(i, m)
            Else
                wsMonthlyW.Cells(outRowMonthly, i + 1).Value = 0
            End If
        Next i
        
        wsMonthlyW.Cells(outRowMonthly, zoneCount + 2).Value = Round(monthTotal, 2)
        outRowMonthly = outRowMonthly + 1
    Next m
    
    ' 年平均行（直接从汇总行的segWSum/segWCnt读取，与纳污能力结果完全一致）
    wsMonthlyW.Cells(outRowMonthly, 1).Value = "年平均"
    monthTotal = 0
    Dim sumSegIdx As Long
    For i = 1 To zoneCount
        ' 汇总行是最后一个段
        sumSegIdx = zoneSegCount(i)
        If sumSegIdx > 0 And segWCnt(i, sumSegIdx) > 0 Then
            dailyW = segWSum(i, sumSegIdx) / segWCnt(i, sumSegIdx)
        Else
            dailyW = 0
        End If
        wsMonthlyW.Cells(outRowMonthly, i + 1).Value = Round(dailyW, 2)
        monthTotal = monthTotal + dailyW
    Next i
    wsMonthlyW.Cells(outRowMonthly, zoneCount + 2).Value = Round(monthTotal, 2)
    
    ' 设置逐月表格式
    wsMonthlyW.Range(wsMonthlyW.Cells(2, 1), wsMonthlyW.Cells(outRowMonthly, zoneCount + 2)).Interior.Color = COLOR_AUTO
    wsMonthlyW.Range(wsMonthlyW.Cells(outRowMonthly, 1), wsMonthlyW.Cells(outRowMonthly, zoneCount + 2)).Font.Bold = True
    wsMonthlyW.Range(wsMonthlyW.Cells(outRowMonthly, 1), wsMonthlyW.Cells(outRowMonthly, zoneCount + 2)).Interior.Color = RGB(220, 230, 241)
    
    ' ========== 创建过程版和结果版 Sheet（从分段汇总数组取年平均） ==========
    
    ' Sheet1: 纳污能力过程（详细版）
    Dim wsProcess As Worksheet
    Set wsProcess = GetOrCreateSheet("纳污能力过程" & schemeSuffix)
    wsProcess.Cells.Clear
    
    ' 过程版表头
    wsProcess.Cells(1, 1).Value = "功能区"
    wsProcess.Cells(1, 2).Value = "河段名称"
    wsProcess.Cells(1, 3).Value = "类型"
    wsProcess.Cells(1, 4).Value = "长度L(m)"
    wsProcess.Cells(1, 5).Value = "流量Q(m3/s)"
    wsProcess.Cells(1, 6).Value = "入口C0"
    wsProcess.Cells(1, 7).Value = "出口C"
    wsProcess.Cells(1, 8).Value = "纳污能力(t/a)"
    wsProcess.Cells(1, 9).Value = "备注"
    wsProcess.Range("A1:I1").Interior.Color = COLOR_AUTO
    wsProcess.Range("A1:I1").Font.Bold = True
    
    wsProcess.Columns("A").ColumnWidth = 12
    wsProcess.Columns("B").ColumnWidth = 16
    wsProcess.Columns("C").ColumnWidth = 8
    wsProcess.Columns("D").ColumnWidth = 12
    wsProcess.Columns("E").ColumnWidth = 14
    wsProcess.Columns("F").ColumnWidth = 10
    wsProcess.Columns("G").ColumnWidth = 10
    wsProcess.Columns("H").ColumnWidth = 14
    wsProcess.Columns("I").ColumnWidth = 24
    
    ' Sheet2: 纳污能力结果（简洁版）
    Set wsResult = GetOrCreateSheet("纳污能力结果" & schemeSuffix)
    wsResult.Cells.Clear
    
    ' 结果版表头（无备注列）
    wsResult.Cells(1, 1).Value = "功能区"
    wsResult.Cells(1, 2).Value = "河段名称"
    wsResult.Cells(1, 3).Value = "类型"
    wsResult.Cells(1, 4).Value = "长度L(m)"
    wsResult.Cells(1, 5).Value = "流量Q(m3/s)"
    wsResult.Cells(1, 6).Value = "入口C0"
    wsResult.Cells(1, 7).Value = "出口C"
    wsResult.Cells(1, 8).Value = "纳污能力(t/a)"
    wsResult.Range("A1:H1").Interior.Color = COLOR_AUTO
    wsResult.Range("A1:H1").Font.Bold = True
    
    wsResult.Columns("A").ColumnWidth = 12
    wsResult.Columns("B").ColumnWidth = 16
    wsResult.Columns("C").ColumnWidth = 8
    wsResult.Columns("D").ColumnWidth = 12
    wsResult.Columns("E").ColumnWidth = 14
    wsResult.Columns("F").ColumnWidth = 10
    wsResult.Columns("G").ColumnWidth = 10
    wsResult.Columns("H").ColumnWidth = 14
    
    ' ========== 从分段汇总数组输出（与逐日逐月一致） ==========
    Dim outRowProcess As Long
    Dim outRowResult As Long
    Dim avgQ As Double, avgC0 As Double, avgCout As Double, avgW As Double
    Dim segType As String
    
    outRowProcess = 2
    outRowResult = 2
    
    For i = 1 To zoneCount
        If zoneSegCount(i) > 0 Then
            ' ========== 输出到过程版（全部内容） ==========
            For seg = 1 To zoneSegCount(i)
                wsProcess.Cells(outRowProcess, 1).Value = zones(i).Name
                wsProcess.Cells(outRowProcess, 2).Value = segInfoName(i, seg)
                wsProcess.Cells(outRowProcess, 3).Value = segInfoType(i, seg)
                segType = segInfoType(i, seg)
                
                ' 长度（固定值）
                If segInfoLength(i, seg) > 0 Then
                    wsProcess.Cells(outRowProcess, 4).Value = segInfoLength(i, seg)
                Else
                    wsProcess.Cells(outRowProcess, 4).Value = "-"
                End If
                
                ' 流量年平均
                If segWCnt(i, seg) > 0 Then
                    avgQ = segQSum(i, seg) / segWCnt(i, seg)
                    avgC0 = segC0Sum(i, seg) / segWCnt(i, seg)
                    avgCout = segCoutSum(i, seg) / segWCnt(i, seg)
                    avgW = segWSum(i, seg) / segWCnt(i, seg)
                Else
                    avgQ = 0: avgC0 = 0: avgCout = 0: avgW = 0
                End If
                
                If avgQ > 0 Then
                    wsProcess.Cells(outRowProcess, 5).Value = Round(avgQ, 3)
                Else
                    wsProcess.Cells(outRowProcess, 5).Value = "-"
                End If
                
                If segType <> "汇总" Then
                    wsProcess.Cells(outRowProcess, 6).Value = Round(avgC0, 4)
                Else
                    wsProcess.Cells(outRowProcess, 6).Value = "-"
                End If
                
                If avgCout > 0 Or segType = "干流段" Then
                    wsProcess.Cells(outRowProcess, 7).Value = Round(avgCout, 4)
                Else
                    wsProcess.Cells(outRowProcess, 7).Value = "-"
                End If
                
                If segType = "干流段" Or segType = "支流" Or segType = "汇总" Then
                    wsProcess.Cells(outRowProcess, 8).Value = Round(avgW, 2)
                Else
                    wsProcess.Cells(outRowProcess, 8).Value = "-"
                End If
                
                wsProcess.Cells(outRowProcess, 9).Value = segInfoRemark(i, seg)
                
                ' 过程版颜色
                If segType = "汇总" Then
                    wsProcess.Range(wsProcess.Cells(outRowProcess, 1), wsProcess.Cells(outRowProcess, 9)).Font.Bold = True
                    wsProcess.Range(wsProcess.Cells(outRowProcess, 1), wsProcess.Cells(outRowProcess, 9)).Interior.Color = RGB(220, 230, 241)
                ElseIf segType = "混合" Then
                    wsProcess.Range(wsProcess.Cells(outRowProcess, 1), wsProcess.Cells(outRowProcess, 9)).Interior.Color = RGB(255, 242, 204)
                ElseIf segType = "支流" Then
                    wsProcess.Range(wsProcess.Cells(outRowProcess, 1), wsProcess.Cells(outRowProcess, 9)).Interior.Color = RGB(226, 239, 218)
                End If
                
                outRowProcess = outRowProcess + 1
            Next seg
            
            ' 过程版空行分隔
            outRowProcess = outRowProcess + 1
            
            ' ========== 输出到结果版（只有干流段和汇总） ==========
            For seg = 1 To zoneSegCount(i)
                segType = segInfoType(i, seg)
                If segType = "干流段" Or segType = "汇总" Then
                    wsResult.Cells(outRowResult, 1).Value = zones(i).Name
                    
                    ' 汇总行名称简化
                    If segType = "汇总" Then
                        wsResult.Cells(outRowResult, 2).Value = zones(i).Name & "合计"
                        wsResult.Cells(outRowResult, 3).Value = "汇总"
                    Else
                        wsResult.Cells(outRowResult, 2).Value = segInfoName(i, seg)
                        wsResult.Cells(outRowResult, 3).Value = "干流段"
                    End If
                    
                    ' 长度
                    If segInfoLength(i, seg) > 0 Then
                        wsResult.Cells(outRowResult, 4).Value = segInfoLength(i, seg)
                    Else
                        wsResult.Cells(outRowResult, 4).Value = "-"
                    End If
                    
                    ' 流量年平均
                    If segWCnt(i, seg) > 0 Then
                        avgQ = segQSum(i, seg) / segWCnt(i, seg)
                        avgC0 = segC0Sum(i, seg) / segWCnt(i, seg)
                        avgCout = segCoutSum(i, seg) / segWCnt(i, seg)
                        avgW = segWSum(i, seg) / segWCnt(i, seg)
                    Else
                        avgQ = 0: avgC0 = 0: avgCout = 0: avgW = 0
                    End If
                    
                    If avgQ > 0 Then
                        wsResult.Cells(outRowResult, 5).Value = Round(avgQ, 3)
                    Else
                        wsResult.Cells(outRowResult, 5).Value = "-"
                    End If
                    
                    wsResult.Cells(outRowResult, 6).Value = Round(avgC0, 4)
                    wsResult.Cells(outRowResult, 7).Value = Round(avgCout, 4)
                    wsResult.Cells(outRowResult, 8).Value = Round(avgW, 2)
                    
                    ' 结果版汇总行加粗
                    If segType = "汇总" Then
                        wsResult.Range(wsResult.Cells(outRowResult, 1), wsResult.Cells(outRowResult, 8)).Font.Bold = True
                        wsResult.Range(wsResult.Cells(outRowResult, 1), wsResult.Cells(outRowResult, 8)).Interior.Color = RGB(220, 230, 241)
                    End If
                    
                    outRowResult = outRowResult + 1
                End If
            Next seg
        End If
    Next i
End Sub

' ============================================================
' 计算功能区纳污能力（简化版，只返回总值）
' ============================================================
Private Function CalcZoneCapacity(zone As ZoneInfo) As Double
    Dim totalW As Double
    totalW = 0
    
    ' 如果没有支流，整段干流计算
    If zone.BranchCount = 0 Then
        totalW = CalcSegmentCapacity(zone.MainQ, zone.MainLength, zone.MainC0, zone)
        CalcZoneCapacity = totalW
        Exit Function
    End If
    
    ' 按汇入位置排序支流
    Dim sortedIdx() As Long
    ReDim sortedIdx(1 To zone.BranchCount)
    
    Dim j As Long, k As Long, tmp As Long
    For j = 1 To zone.BranchCount
        sortedIdx(j) = j
    Next j
    
    For j = 1 To zone.BranchCount - 1
        For k = j + 1 To zone.BranchCount
            If zone.Branches(sortedIdx(k)).JoinPosition < zone.Branches(sortedIdx(j)).JoinPosition Then
                tmp = sortedIdx(j)
                sortedIdx(j) = sortedIdx(k)
                sortedIdx(k) = tmp
            End If
        Next k
    Next j
    
    ' 分段计算
    Dim currentPos As Double
    Dim currentQ As Double
    Dim currentC As Double
    Dim segLength As Double
    Dim segW As Double
    Dim segC_out As Double
    Dim branchC_out As Double
    Dim branchIdx As Long
    Dim branchQ As Double
    Dim branchC As Double
    
    currentPos = 0
    currentQ = zone.MainQ
    currentC = zone.MainC0
    
    For j = 1 To zone.BranchCount
        branchIdx = sortedIdx(j)
        
        ' 干流段
        segLength = zone.Branches(branchIdx).JoinPosition - currentPos
        
        If segLength > 0 Then
            segC_out = CalcOutflowConc(currentC, zone.K, segLength, CalcVelocity(currentQ, zone.a, zone.beta))
            segW = CalcSegmentCapacity(currentQ, segLength, currentC, zone)
            totalW = totalW + segW
            currentC = segC_out
        End If
        
        ' 支流出流浓度
        branchQ = zone.Branches(branchIdx).Q
        branchC = zone.Branches(branchIdx).C0
        
        If branchQ > 0 And zone.Branches(branchIdx).Length > 0 Then
            branchC_out = CalcOutflowConc(branchC, zone.K, zone.Branches(branchIdx).Length, _
                                          CalcVelocity(branchQ, zone.a, zone.beta))
        Else
            branchC_out = branchC
        End If
        
        ' 混合
        If branchQ > 0 Then
            Dim mixedC As Double
            mixedC = (currentQ * currentC + branchQ * branchC_out) / (currentQ + branchQ)
            currentQ = currentQ + branchQ
            currentC = mixedC
        End If
        
        currentPos = zone.Branches(branchIdx).JoinPosition
    Next j
    
    ' 最后一段干流
    segLength = zone.MainLength - currentPos
    
    If segLength > 0 Then
        segW = CalcSegmentCapacity(currentQ, segLength, currentC, zone)
        totalW = totalW + segW
    End If
    
    CalcZoneCapacity = totalW
End Function

' ============================================================
' 计算功能区分段详情（核心函数）
' ============================================================
Private Sub CalcZoneSegments(zone As ZoneInfo, ByRef segments() As SegmentResult, ByRef segCount As Long)
    ' 最大段数 = 支流数×2 + 2（首尾干流段） + 1（汇总）
    Dim maxSegs As Long
    maxSegs = zone.BranchCount * 2 + 3
    ReDim segments(1 To maxSegs)
    segCount = 0
    
    Dim mainTotalW As Double  ' 只汇总干流段
    Dim totalLength As Double
    Dim finalC_out As Double
    mainTotalW = 0
    totalLength = 0
    
    ' 如果没有支流，整段干流计算
    If zone.BranchCount = 0 Then
        segCount = segCount + 1
        segments(segCount).Name = zone.MainName
        segments(segCount).SegType = "干流段"
        segments(segCount).Length = zone.MainLength
        segments(segCount).Q = zone.MainQ
        segments(segCount).C0 = zone.MainC0
        segments(segCount).C_out = CalcOutflowConc(zone.MainC0, zone.K, zone.MainLength, _
                                                   CalcVelocity(zone.MainQ, zone.a, zone.beta))
        segments(segCount).W = CalcSegmentCapacity(zone.MainQ, zone.MainLength, zone.MainC0, zone)
        segments(segCount).Remark = "全段"
        
        mainTotalW = segments(segCount).W
        totalLength = zone.MainLength
        finalC_out = segments(segCount).C_out
        
        ' 汇总行
        segCount = segCount + 1
        segments(segCount).Name = "【" & zone.Name & " 小计】"
        segments(segCount).SegType = "汇总"
        segments(segCount).Length = totalLength
        segments(segCount).Q = 0
        segments(segCount).C0 = zone.MainC0
        segments(segCount).C_out = finalC_out
        segments(segCount).W = mainTotalW
        segments(segCount).Remark = "仅汇总干流段"
        
        Exit Sub
    End If
    
    ' 按汇入位置排序支流
    Dim sortedIdx() As Long
    ReDim sortedIdx(1 To zone.BranchCount)
    
    Dim j As Long, k As Long, tmp As Long
    For j = 1 To zone.BranchCount
        sortedIdx(j) = j
    Next j
    
    For j = 1 To zone.BranchCount - 1
        For k = j + 1 To zone.BranchCount
            If zone.Branches(sortedIdx(k)).JoinPosition < zone.Branches(sortedIdx(j)).JoinPosition Then
                tmp = sortedIdx(j)
                sortedIdx(j) = sortedIdx(k)
                sortedIdx(k) = tmp
            End If
        Next k
    Next j
    
    ' 分段计算
    Dim currentPos As Double
    Dim currentQ As Double
    Dim currentC As Double
    Dim segLength As Double
    Dim segW As Double
    Dim segC_out As Double
    Dim branchW As Double
    Dim branchC_out As Double
    Dim branchIdx As Long
    Dim branchQ As Double
    Dim branchC As Double
    Dim segNum As Long
    
    currentPos = 0
    currentQ = zone.MainQ
    currentC = zone.MainC0
    segNum = 0
    
    For j = 1 To zone.BranchCount
        branchIdx = sortedIdx(j)
        segNum = segNum + 1
        
        ' 干流段（从 currentPos 到汇入点）
        segLength = zone.Branches(branchIdx).JoinPosition - currentPos
        
        If segLength > 0 Then
            segC_out = CalcOutflowConc(currentC, zone.K, segLength, CalcVelocity(currentQ, zone.a, zone.beta))
            segW = CalcSegmentCapacity(currentQ, segLength, currentC, zone)
            
            segCount = segCount + 1
            segments(segCount).Name = zone.MainName & "-段" & segNum
            segments(segCount).SegType = "干流段"
            segments(segCount).Length = segLength
            segments(segCount).Q = currentQ
            segments(segCount).C0 = currentC
            segments(segCount).C_out = segC_out
            segments(segCount).W = segW
            If j = 1 Then
                segments(segCount).Remark = "起点→" & zone.Branches(branchIdx).Name & "汇入点"
            Else
                segments(segCount).Remark = "上一汇入点→" & zone.Branches(branchIdx).Name & "汇入点"
            End If
            
            mainTotalW = mainTotalW + segW
            totalLength = totalLength + segLength
            currentC = segC_out
        End If
        
        ' 支流
        branchQ = zone.Branches(branchIdx).Q
        branchC = zone.Branches(branchIdx).C0
        
        If branchQ > 0 And zone.Branches(branchIdx).Length > 0 Then
            branchC_out = CalcOutflowConc(branchC, zone.K, zone.Branches(branchIdx).Length, _
                                          CalcVelocity(branchQ, zone.a, zone.beta))
            branchW = CalcSegmentCapacity(branchQ, zone.Branches(branchIdx).Length, branchC, zone)
            
            segCount = segCount + 1
            segments(segCount).Name = zone.Branches(branchIdx).Name
            segments(segCount).SegType = "支流"
            segments(segCount).Length = zone.Branches(branchIdx).Length
            segments(segCount).Q = branchQ
            segments(segCount).C0 = branchC
            segments(segCount).C_out = branchC_out
            segments(segCount).W = branchW
            segments(segCount).Remark = "(不计入汇总)"
        Else
            branchC_out = branchC
            branchW = 0
        End If
        
        ' 混合点
        If branchQ > 0 Then
            Dim mixedC As Double
            Dim mixedQ As Double
            mixedQ = currentQ + branchQ
            mixedC = (currentQ * currentC + branchQ * branchC_out) / mixedQ
            
            segCount = segCount + 1
            segments(segCount).Name = "(混合点" & j & ")"
            segments(segCount).SegType = "混合"
            segments(segCount).Length = 0
            segments(segCount).Q = mixedQ
            segments(segCount).C0 = mixedC
            segments(segCount).C_out = 0
            segments(segCount).W = 0
            segments(segCount).Remark = "Q=" & Round(currentQ, 2) & "×C=" & Round(currentC, 4) & _
                                        " + Q=" & Round(branchQ, 2) & "×C=" & Round(branchC_out, 4)
            
            currentQ = mixedQ
            currentC = mixedC
        End If
        
        currentPos = zone.Branches(branchIdx).JoinPosition
    Next j
    
    ' 最后一段干流（最后汇入点 → 终点）
    segLength = zone.MainLength - currentPos
    
    If segLength > 0 Then
        segNum = segNum + 1
        segC_out = CalcOutflowConc(currentC, zone.K, segLength, CalcVelocity(currentQ, zone.a, zone.beta))
        segW = CalcSegmentCapacity(currentQ, segLength, currentC, zone)
        
        segCount = segCount + 1
        segments(segCount).Name = zone.MainName & "-段" & segNum
        segments(segCount).SegType = "干流段"
        segments(segCount).Length = segLength
        segments(segCount).Q = currentQ
        segments(segCount).C0 = currentC
        segments(segCount).C_out = segC_out
        segments(segCount).W = segW
        segments(segCount).Remark = "最后汇入点→终点"
        
        mainTotalW = mainTotalW + segW
        totalLength = totalLength + segLength
        finalC_out = segC_out
    Else
        finalC_out = currentC
    End If
    
    ' 汇总行（只汇总干流段）
    segCount = segCount + 1
    segments(segCount).Name = "【" & zone.Name & " 小计】"
    segments(segCount).SegType = "汇总"
    segments(segCount).Length = totalLength
    segments(segCount).Q = 0
    segments(segCount).C0 = zone.MainC0
    segments(segCount).C_out = finalC_out
    segments(segCount).W = mainTotalW
    segments(segCount).Remark = "仅汇总干流段"
End Sub

' ============================================================
' 在列名数组中查找名称对应的索引
' ============================================================
Private Function FindColIdx(colNames() As String, cnt As Long, targetName As String) As Long
    Dim i As Long
    FindColIdx = 0
    For i = 1 To cnt
        If colNames(i) = targetName Then
            FindColIdx = i
            Exit Function
        End If
    Next i
End Function

' ============================================================
' 计算单段纳污能力
' ============================================================
Private Function CalcSegmentCapacity(Q As Double, L As Double, C0 As Double, zone As ZoneInfo) As Double
    If Q <= 0 Or L <= 0 Then
        CalcSegmentCapacity = 0
        Exit Function
    End If
    
    Dim u As Double
    u = CalcVelocity(Q, zone.a, zone.beta)
    
    If u <= 0 Then
        CalcSegmentCapacity = 0
        Exit Function
    End If
    
    Dim decay As Double
    decay = Exp(-zone.K * L / u)
    
    If decay >= 0.9999999999 Then
        CalcSegmentCapacity = 0
        Exit Function
    End If
    
    Dim concTerm As Double
    concTerm = zone.Cs - C0 * decay
    
    Dim flowTerm As Double
    flowTerm = (Q * zone.K * L / u) / (1 - decay)
    
    CalcSegmentCapacity = UNIT_FACTOR * zone.b * concTerm * flowTerm
End Function

' ============================================================
' 计算流速: u = a × Q^β
' ============================================================
Private Function CalcVelocity(Q As Double, a As Double, beta As Double) As Double
    If Q <= 0 Or a <= 0 Then
        CalcVelocity = 0
    Else
        CalcVelocity = a * (Q ^ beta)
    End If
End Function

' ============================================================
' 计算出流浓度: C_out = C0 × exp(-K×L/u)
' ============================================================
Private Function CalcOutflowConc(C0 As Double, K As Double, L As Double, u As Double) As Double
    If u <= 0 Or L <= 0 Then
        CalcOutflowConc = C0
    Else
        CalcOutflowConc = C0 * Exp(-K * L / u)
    End If
End Function

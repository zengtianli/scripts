(defun c:DEBUGPOLYVERTEX ()
  (princ "\n=== 检查POLYLINE和其VERTEX子实体 ===")
  
  ; 选择所有POLYLINE
  (setq ss (ssget "X" '((0 . "POLYLINE"))))
  
  (if ss
    (progn
      (princ (strcat "\n找到 " (itoa (sslength ss)) " 个POLYLINE"))
      
      ; 检查前3个POLYLINE的详细信息
      (setq max-show (min 3 (sslength ss)))
      (setq i 0)
      (while (< i max-show)
        (setq ent (ssname ss i))
        (setq entdata (entget ent))  ; 移除了错误的参数
        
        (princ (strcat "\n\n--- POLYLINE " (itoa (1+ i)) " ---"))
        (princ (strcat "\n句柄: " (cdr (assoc 5 entdata))))
        (princ (strcat "\n图层: " (cdr (assoc 8 entdata))))
        
        ; 显示关键DXF代码
        (princ "\n关键DXF代码:")
        (foreach dxf-pair entdata
          (setq code (car dxf-pair))
          (setq value (cdr dxf-pair))
          (if (member code '(10 20 30 38 39 70 71))  ; 重要的坐标和标志
            (princ (strcat "\n  " (itoa code) ": " (vl-prin1-to-string value)))
          )
        )
        
        ; 查找VERTEX子实体
        (princ "\n\nVERTEX子实体:")
        (setq vertex-ent (entnext ent))
        (setq vertex-count 0)
        
        (while (and vertex-ent 
                    (setq vertex-data (entget vertex-ent))
                    (= (cdr (assoc 0 vertex-data)) "VERTEX")
                    (< vertex-count 5))  ; 只显示前5个vertex
          
          (setq vertex-count (1+ vertex-count))
          
          (princ (strcat "\n  VERTEX " (itoa vertex-count) ":"))
          (princ (strcat "\n    句柄: " (cdr (assoc 5 vertex-data))))
          
          ; 检查坐标
          (setq x-coord (cdr (assoc 10 vertex-data)))
          (setq y-coord (cdr (assoc 20 vertex-data)))
          (setq z-coord (cdr (assoc 30 vertex-data)))
          
          (if x-coord (princ (strcat "\n    X: " (rtos x-coord 2 4))))
          (if y-coord (princ (strcat "\n    Y: " (rtos y-coord 2 4))))
          (if z-coord (princ (strcat "\n    Z: " (rtos z-coord 2 4)))
                      (princ "\n    Z: 无"))
          
          ; 检查elevation (38)
          (setq elevation (cdr (assoc 38 vertex-data)))
          (if elevation 
            (princ (strcat "\n    Elevation: " (rtos elevation 2 4)))
            (princ "\n    Elevation: 无")
          )
          
          ; 显示所有VERTEX的DXF代码（前10个）
          (princ "\n    所有DXF代码:")
          (setq j 0)
          (foreach dxf-pair vertex-data
            (if (< j 10)
              (princ (strcat "\n      " (itoa (car dxf-pair)) ": " (vl-prin1-to-string (cdr dxf-pair))))
            )
            (setq j (1+ j))
          )
          
          (setq vertex-ent (entnext vertex-ent))
        )
        
        (if (> vertex-count 0)
          (princ (strcat "\n  共找到VERTEX子实体 (仅显示前5个)"))
          (princ "\n  未找到VERTEX子实体")
        )
        
        (setq i (1+ i))
      )
    )
    (princ "\n未找到POLYLINE对象")
  )
  (princ)
)


(defun c:MOVEPOLYBYELEVATION ()
  (princ "\n=== 根据Z坐标移动POLYLINE到对应图层 ===")
  
  (setq ss (ssget "X" '((0 . "POLYLINE"))))
  (setq count 0)
  
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq entdata (entget ent))
        
        ; 获取Z坐标作为elevation
        (setq main-point (cdr (assoc 10 entdata)))
        (if main-point
          (progn
            (setq z-coord (caddr main-point))  ; 第三个元素是Z坐标
            (setq elev-int (fix z-coord))      ; 转为整数
            (setq layername (strcat "dgx" (itoa elev-int)))
            
            ; 创建图层如果不存在
            (if (not (tblsearch "LAYER" layername))
              (command "-LAYER" "NEW" layername "")
            )
            
            ; 移动到对应图层
            (setq newentdata (subst (cons 8 layername) (assoc 8 entdata) entdata))
            (entmod newentdata)
            (setq count (1+ count))
            (princ (strcat "\n移动Z=" (rtos z-coord 2 0) " 到图层 " layername))
          )
        )
        (setq i (1+ i))
      )
      (princ (strcat "\n\n总共移动了 " (itoa count) " 个POLYLINE"))
    )
    (princ "\n未找到POLYLINE对象")
  )
  (princ)
)


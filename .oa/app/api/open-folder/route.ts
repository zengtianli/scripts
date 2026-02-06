import { NextRequest, NextResponse } from 'next/server'
import { exec } from 'child_process'
import path from 'path'

export async function POST(request: NextRequest) {
  try {
    const { filePath } = await request.json()

    if (!filePath) {
      return NextResponse.json({ error: '缺少文件路径' }, { status: 400 })
    }

    // 获取文件所在目录
    const folderPath = path.dirname(filePath)

    // 用 Finder 打开目录并选中文件
    exec(`open -R "${filePath}"`, (error) => {
      if (error) {
        // 如果失败，直接打开目录
        exec(`open "${folderPath}"`)
      }
    })

    return NextResponse.json({ success: true, folder: folderPath })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}

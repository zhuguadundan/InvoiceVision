import sys, fitz
from os import path, makedirs
import datetime
import os

class pdf2img:
    def pyMuPDF_fitz(self, pdfPath):
        self.imagePath = ''
        startTime_pdf2img = datetime.datetime.now()  # 开始时间
        
        # 修正路径分隔符处理，避免中文路径问题
        if '\\' in pdfPath:
            filename = pdfPath.split('\\')[-1]
        else:
            filename = pdfPath.split('/')[-1]
        
        # 清理文件名，避免特殊字符和中文字符
        import re
        import hashlib
        
        # 移除文件扩展名
        base_filename = filename[:-4] if filename.endswith('.pdf') else filename
        
        # 更智能的文件名处理，支持中文字符
        # 首先尝试保留原文件名，只替换系统不支持的字符
        invalid_chars = r'[<>:"/\\|?*]'
        clean_filename = re.sub(invalid_chars, '_', base_filename)
        
        # 如果文件名过长，截取前面部分并添加哈希
        if len(clean_filename.encode('utf-8')) > 100:  # 考虑中文字符占用字节
            # 保留前30个字符，添加哈希值确保唯一性
            hash_suffix = hashlib.md5(base_filename.encode('utf-8')).hexdigest()[:8]
            clean_filename = clean_filename[:30] + "_" + hash_suffix
        
        # 如果清理后的文件名为空，使用哈希值
        if not clean_filename.strip() or len(clean_filename) < 1:
            clean_filename = hashlib.md5(base_filename.encode('utf-8')).hexdigest()[:12]
            
        self.imagePath = f'IMG/{clean_filename}'
        
        try:
            pdfDoc = fitz.open(pdfPath)
            # 修复API变化：pageCount -> page_count
            page_count = pdfDoc.page_count
            
            print(f"PDF页数: {page_count}")
            
            for pg in range(page_count):
                page = pdfDoc[pg]
                rotate = int(0)
                # 每个尺寸的缩放系数为2，生成高分辨率图像
                zoom_x = 2  # 提高分辨率
                zoom_y = 2
                # 修复API变化：preRotate -> prerotate
                try:
                    mat = fitz.Matrix(zoom_x, zoom_y).prerotate(rotate)
                except AttributeError:
                    # 兼容旧版本API
                    mat = fitz.Matrix(zoom_x, zoom_y).preRotate(rotate)
                
                # 修复API变化：getPixmap -> get_pixmap
                try:
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                except AttributeError:
                    # 兼容旧版本API
                    pix = page.getPixmap(matrix=mat, alpha=False)

                if not path.exists(self.imagePath):  # 判断存放图片的文件夹是否存在
                    makedirs(self.imagePath)  # 若图片文件夹不存在就创建

                # 修复API变化：writePNG -> save (在新版本中)
                output_file = os.path.join(self.imagePath, f'images_{pg:03d}.png')
                try:
                    pix.save(output_file)
                except AttributeError:
                    # 兼容旧版本API
                    pix.writePNG(output_file)
                    
                print(f"转换页面 {pg+1}/{page_count}: {output_file}")

            pdfDoc.close()
            
        except Exception as e:
            print(f"PDF处理出错: {e}")
            raise
            
        endTime_pdf2img = datetime.datetime.now()  # 结束时间
        print(f'PDF转图片耗时: {(endTime_pdf2img - startTime_pdf2img).seconds}秒')
        return self.imagePath


if __name__ == "__main__":
    pdfPath = 'INV/InvoiceColored.PDF'
    Topdf = pdf2img()
    Topdf.pyMuPDF_fitz(pdfPath)
    print(Topdf.imagePath)


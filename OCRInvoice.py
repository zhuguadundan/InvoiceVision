#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鏀寔绂荤嚎杩愯鐨凮CRInvoice绫?- PaddleOCR 3.1+ 绂荤嚎鐗?(澶栭儴妯″瀷鏋舵瀯)
浣跨敤寤惰繜瀵煎叆閬垮厤鎵撳寘鏃剁殑妯″潡渚濊禆闂
"""

# 寤惰繜瀵煎叆 - 閬垮厤鍚姩鏃跺氨鍔犺浇PaddleOCR
# from paddleocr import PaddleOCR  # 绉诲埌浣跨敤鏃跺鍏?
import re
import sys
from PIL import Image
import os
import json
import numpy as np
import cv2
from pathlib import Path
import threading
import time

def safe_print(text):
    """瀹夊叏鐨勬墦鍗板嚱鏁帮紝澶勭悊缂栫爜闂"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('gbk', 'ignore').decode('gbk'))

class OfflineOCRInvoice:
    # 绫诲彉閲忥細鎵€鏈夊疄渚嬪叡浜殑OCR寮曟搸
    _shared_ocr_engine = None
    _initialization_lock = threading.Lock()
    _initialization_status = "pending"  # pending, loading, ready, failed
    
    def __init__(self):
        """鍒濆鍖栫绾縊CR鍙戠エ璇嗗埆鍣?""
        self.precision_mode = '蹇€?
        self.offline_config = self._load_offline_config()
        
        # 纭繚鍏ㄥ眬OCR寮曟搸宸插垵濮嬪寲
        if self.__class__._initialization_status == "pending":
            self.global_initialize_ocr()
        
    def _load_offline_config(self):
        """鍔犺浇绂荤嚎閰嶇疆 - 鏀寔澶栭儴妯″瀷鏋舵瀯"""
        try:
            # 瀵煎叆resource_utils妯″潡锛屾敮鎸佹墦鍖呯幆澧?
            import resource_utils
            base_dir = Path(resource_utils.get_resource_path("."))
            config_file = Path(resource_utils.get_config_path())
            # 浣跨敤resource_utils鑾峰彇姝ｇ‘鐨勬ā鍨嬭矾寰?
            models_path = Path(resource_utils.get_models_path())
        except ImportError:
            # 闄嶇骇鍒板師濮嬮€昏緫
            base_dir = Path(__file__).parent
            config_file = base_dir / "offline_config.json"
            models_path = base_dir / "models"
        
        # 榛樿閰嶇疆
        default_config = {
            "offline_mode": True,
            "use_gpu": False,
            "lang": "ch",
            "models_path": str(models_path)
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 鍚堝苟榛樿閰嶇疆
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                        
            except Exception as e:
                print(f"閰嶇疆鏂囦欢鍔犺浇澶辫触锛屼娇鐢ㄩ粯璁ら厤缃? {e}")
                config = default_config
        else:
            config = default_config
            
        # 浣跨敤resource_utils鎻愪緵鐨勬ā鍨嬭矾寰勶紝瑕嗙洊閰嶇疆鏂囦欢涓殑鐩稿璺緞
        config["models_path"] = str(models_path)
        
        # 鏋勫缓妯″瀷璺緞 - 浣跨敤姝ｇ‘鐨刴odels_path
        if "models" not in config:
            config["models"] = {
                "cls_model_dir": str(models_path / "PP-LCNet_x1_0_textline_ori"),
                "det_model_dir": str(models_path / "PP-OCRv5_server_det"),
                "rec_model_dir": str(models_path / "PP-OCRv5_server_rec")
            }
        else:
            # 纭繚妯″瀷璺緞涓虹粷瀵硅矾寰勶紝浣跨敤姝ｇ‘鐨刴odels_path
            for key, model_path in config["models"].items():
                model_name = Path(model_path).name
                config["models"][key] = str(models_path / model_name)
        
        return config
    
    def check_models_available(self):
        """妫€鏌ユā鍨嬫枃浠舵槸鍚﹀彲鐢?""
        if not self.offline_config or "models" not in self.offline_config:
            return False, "閰嶇疆鏂囦欢涓湭鎵惧埌妯″瀷閰嶇疆"
            
        print(f"[DEBUG] 妯″瀷鍩虹璺緞: {self.offline_config.get('models_path', 'N/A')}")
        
        missing_models = []
        incomplete_models = []
        
        for model_name, model_path in self.offline_config["models"].items():
            print(f"[DEBUG] 妫€鏌ユā鍨?{model_name}: {model_path}")
            
            if not os.path.exists(model_path):
                missing_models.append(f"{model_name}: {model_path}")
                print(f"  [ERROR] 璺緞涓嶅瓨鍦?)
            else:
                # 妫€鏌ユā鍨嬫枃浠舵槸鍚﹀畬鏁?
                try:
                    files = os.listdir(model_path)
                    # 鏀寔涓ょ妯″瀷鏍煎紡锛氭柊鏍煎紡(inference.json)鍜屾棫鏍煎紡(inference.pdmodel)
                    required_files_new = ['inference.json', 'inference.pdiparams']  # 鏂版牸寮?
                    required_files_old = ['inference.pdmodel', 'inference.pdiparams']  # 鏃ф牸寮?
                    
                    missing_files_new = [f for f in required_files_new if f not in files]
                    missing_files_old = [f for f in required_files_old if f not in files]
                    
                    if not missing_files_new:
                        print(f"  [OK] 妯″瀷鏂囦欢瀹屾暣 (鏂版牸寮?")
                        print(f"    鏂囦欢鍒楄〃: {files}")
                    elif not missing_files_old:
                        print(f"  [OK] 妯″瀷鏂囦欢瀹屾暣 (鏃ф牸寮?")
                        print(f"    鏂囦欢鍒楄〃: {files}")
                    else:
                        incomplete_models.append(f"{model_name}: 缂哄皯鏂囦欢 (鏂版牸寮忛渶瑕亄missing_files_new} 鎴?鏃ф牸寮忛渶瑕亄missing_files_old})")
                        print(f"  [ERROR] 缂哄皯蹇呴渶鏂囦欢:")
                        print(f"    鏂版牸寮忕己灏? {missing_files_new}")
                        print(f"    鏃ф牸寮忕己灏? {missing_files_old}")
                        print(f"    褰撳墠鏂囦欢: {files}")
                except Exception as e:
                    incomplete_models.append(f"{model_name}: 璇诲彇閿欒 {e}")
                    print(f"  [ERROR] 璇诲彇閿欒: {e}")
                
        error_messages = []
        if missing_models:
            error_messages.append("缂哄皯妯″瀷鏂囦欢澶?\n" + "\n".join(missing_models))
        if incomplete_models:
            error_messages.append("妯″瀷鏂囦欢涓嶅畬鏁?\n" + "\n".join(incomplete_models))
            
        if error_messages:
            return False, "\n\n".join(error_messages)
            
        return True, "鎵€鏈夋ā鍨嬫枃浠跺凡灏辩华"
    
    @classmethod
    def global_initialize_ocr(cls, precision_mode='蹇€?):
        """鍏ㄥ眬OCR寮曟搸鍒濆鍖?- 鍦ㄤ富绾跨▼涓皟鐢紝閬垮厤閲嶅鍒濆鍖?""
        with cls._initialization_lock:
            if cls._initialization_status == "ready":
                print("OCR寮曟搸宸茬粡鍒濆鍖栧畬鎴?)
                return True
            
            if cls._initialization_status == "loading":
                # 绛夊緟鍒濆鍖栧畬鎴?
                print("OCR寮曟搸姝ｅ湪鍒濆鍖栦腑锛岀瓑寰呭畬鎴?..")
                timeout = 30  # 30绉掕秴鏃?
                start_time = time.time()
                while cls._initialization_status == "loading" and time.time() - start_time < timeout:
                    time.sleep(0.1)
                return cls._initialization_status == "ready"
            
            cls._initialization_status = "loading"
            print(f"寮€濮嬪叏灞€鍒濆鍖朞CR寮曟搸锛岀簿搴︽ā寮? {precision_mode}")
            
            try:
                # 鍦ㄤ富绾跨▼涓缃幆澧冨彉閲?- 蹇呴』鍦ㄥ鍏ュ墠璁剧疆
                os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
                os.environ['PADDLE_DISABLE_SHARED_MEM'] = '1'
                os.environ['CUDA_VISIBLE_DEVICES'] = ''
                print("鐜鍙橀噺璁剧疆瀹屾垚")
                
                # 鍒涘缓涓存椂瀹炰緥鑾峰彇閰嶇疆
                temp_instance = cls()
                models_available, message = temp_instance.check_models_available()
                if not models_available:
                    cls._initialization_status = "failed"
                    print(f"妯″瀷妫€鏌ュけ璐? {message}")
                    return False
                
                models = temp_instance.offline_config.get("models", {})
                
                # EasyOCR寮曟搸鍒濆鍖?- PyInstaller鍙嬪ソ
                try:
                    # EasyOCR 宸茬Щ闄わ細寮哄埗杩涘叆 PaddleOCR 鍒濆鍖栧垎鏀?                    raise ImportError("EasyOCR disabled")
                    # EasyOCR 宸茬Щ闄?                    
                    # 鍒涘缓EasyOCR瀹炰緥锛屾敮鎸佷腑鑻辨枃
                    # EasyOCR 宸茬Щ闄わ細涓嶅啀鍒濆鍖?EasyOCR 寮曟搸
                    # EasyOCR 宸茬Щ闄わ細浠ヤ笅鍙傛暟琛屽悓鏃剁Щ闄?                    # EasyOCR 宸茬Щ闄わ細浠ヤ笅鍙傛暟琛屽悓鏃剁Щ闄?                    cls._initialization_status = "ready"
                    # EasyOCR 宸茬Щ闄?                    return True
                    
                except Exception as easyocr_error:
                    # EasyOCR澶辫触锛屽皾璇曞鍏addleOCR浣滀负鍚庡
                    print("EasyOCR 宸茬鐢紝鍒囨崲鍒?PaddleOCR")
                    print("灏濊瘯浣跨敤PaddleOCR浣滀负鍚庡鏂规...")
                    
                    try:
                        from paddleocr import PaddleOCR
                        print("PaddleOCR妯″潡瀵煎叆鎴愬姛")
                        
                        # 浣跨敤瀹樻柟OCR pipeline
                        cls._shared_ocr_engine = PaddleOCR(use_angle_cls=precision_mode == '楂樼簿', 
                                                         lang='ch')
                        cls._initialization_status = "ready"  
                        print("[SUCCESS] 鍏ㄥ眬PaddleOCR寮曟搸鍒濆鍖栨垚鍔?鍚庡妯″紡)")
                        return True
                        
                    except Exception as paddle_error:
                        cls._initialization_status = "failed"
                        print(f"[ERROR] 鎵€鏈塐CR寮曟搸鍒濆鍖栧け璐?)
                        # EasyOCR 宸茬Щ闄?                        print(f"PaddleOCR閿欒: {paddle_error}")
                        return False
                        
            except ImportError as e:
                cls._initialization_status = "failed"
                print(f"[ERROR] OCR妯″潡瀵煎叆澶辫触: {e}")
                return False
            except Exception as e:
                cls._initialization_status = "failed"
                print(f"[ERROR] 鍏ㄥ眬OCR寮曟搸鍒濆鍖栧け璐? {e}")
                print(f"閿欒绫诲瀷: {type(e).__name__}")
                import traceback
                print(f"璇︾粏閿欒淇℃伅:\n{traceback.format_exc()}")
                return False
    
    @property
    def ocr_engine(self):
        """鑾峰彇鍏变韩鐨凮CR寮曟搸瀹炰緥"""
        return self.__class__._shared_ocr_engine
    
    @classmethod
    def get_initialization_status(cls):
        """鑾峰彇鍒濆鍖栫姸鎬?""
        return cls._initialization_status
    
    def initialize_ocr(self):
        """鏃х増鍒濆鍖栨柟娉?- 鐜板湪濮旀墭缁欏叏灞€鍒濆鍖?""
        print("璋冪敤鏃х増initialize_ocr锛屽鎵樼粰鍏ㄥ眬鍒濆鍖?..")
        return self.__class__._shared_ocr_engine is not None
    
    def set_precision_mode(self, mode):
        """璁剧疆绮惧害妯″紡 - 闇€瑕侀噸鏂板叏灞€鍒濆鍖?""
        if mode in ['蹇€?, '楂樼簿']:
            self.precision_mode = mode
            print(f"绮惧害妯″紡璁剧疆涓? {mode}")
            print("娉ㄦ剰: 绮惧害妯″紡鏇存敼闇€瑕侀噸鏂拌皟鐢?global_initialize_ocr() 鎵嶈兘鐢熸晥")
            return True
        else:
            print("鏃犳晥鐨勭簿搴︽ā寮忥紝鏀寔鐨勬ā寮? '蹇€?, '楂樼簿'")
            return False
    
    def run_ocr(self, image_path):
        """鎵цOCR璇嗗埆"""
        # 妫€鏌ュ叏灞€OCR寮曟搸鏄惁鍙敤
        if self.ocr_engine is None:
            print("ERROR: 鍏ㄥ眬OCR寮曟搸鏈垵濮嬪寲锛岃鍏堣皟鐢?OfflineOCRInvoice.global_initialize_ocr()")
            return [image_path, '', '', '', '']
        
        try:
            print(f"寮€濮嬪鐞嗗浘鐗? {os.path.basename(image_path)}")
            
            # 璇诲彇鍥剧墖
            try:
                # 鏂规硶1: 浣跨敤cv2鐩存帴璇诲彇
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                nparr = np.frombuffer(image_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    raise Exception("鍥惧儚瑙ｇ爜澶辫触")
            except:
                # 鏂规硶2: 浣跨敤PIL浣滀负鍚庡鏂规
                from PIL import Image
                pil_image = Image.open(image_path)
                img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # 鎵цOCR璇嗗埆 - 鍏煎EasyOCR鍜孭addleOCR
            if hasattr(self.ocr_engine, 'readtext'):
                # EasyOCR API
                result = self.ocr_engine.readtext(img)
                texts = self._extract_texts_from_result(result)
            else:
                # PaddleOCR API  
                result = self.ocr_engine.ocr(img)
                texts = self._extract_texts_from_result(result)
            
            if not texts:
                print("OCR鏈瘑鍒埌浠讳綍鏂囨湰")
                return [image_path, '', '', '', '']
            
            # 妫€鏌ユ槸鍚﹁瘑鍒埌鍙戠エ鍐呭
            combined_text = '銆? + '銆戙€?.join(texts) + '銆?
            
            if not self._contains_invoice_keywords(combined_text):
                print("鏈娴嬪埌鍙戠エ鍏抽敭璇嶏紝灏濊瘯鏃嬭浆鍥剧墖...")
                img_rotated = cv2.rotate(img, cv2.ROTATE_180)
                
                # 鏃嬭浆鍚庡啀娆CR璇嗗埆 - 鍏煎涓ょAPI
                if hasattr(self.ocr_engine, 'readtext'):
                    # EasyOCR API
                    result = self.ocr_engine.readtext(img_rotated)
                    texts = self._extract_texts_from_result(result)
                else:
                    # PaddleOCR API
                    result = self.ocr_engine.ocr(img_rotated)
                    texts = self._extract_texts_from_result(result)
                    
                combined_text = '銆? + '銆戙€?.join(texts) + '銆?
            
            # 鎻愬彇鍙戠エ淇℃伅
            invoice_info = self._extract_invoice_info(combined_text, image_path)
            print(f"璇嗗埆瀹屾垚: {os.path.basename(image_path)}")
            return invoice_info
            
        except Exception as e:
            print(f"OCR澶勭悊鍑洪敊: {e}")
            return [image_path, '', '', '', '']
    
    def _extract_texts_from_result(self, result):
        """浠嶰CR缁撴灉涓彁鍙栨枃鏈?""
        texts = []
        try:
            if result and len(result) > 0:
                # 妫€鏌ユ柊鏍煎紡鐨勭粨鏋滐紙PaddleX/PaddleOCR鏂扮増鏈級
                if isinstance(result[0], dict) and 'rec_texts' in result[0]:
                    # 鏂扮増鏈牸寮忥細缁撴灉鍖呭惈rec_texts瀛楁
                    texts = result[0]['rec_texts']
                    print("浣跨敤鏂版牸寮忔彁鍙栨枃鏈紝鍏眥}鏉?.format(len(texts)))
                elif result[0]:
                    # 鏃х増鏈牸寮?
                    ocr_result = result[0]
                    for line in ocr_result:
                        if line and len(line) > 1 and line[1]:
                            if isinstance(line[1], tuple) and len(line[1]) > 0:
                                text = line[1][0].strip()
                            elif isinstance(line[1], str):
                                text = line[1].strip()
                            else:
                                continue
                            
                            if text:
                                texts.append(text)
                    print("浣跨敤鏃ф牸寮忔彁鍙栨枃鏈紝鍏眥}鏉?.format(len(texts)))
        except (IndexError, TypeError) as e:
            print(f"鏂囨湰鎻愬彇鍑洪敊: {e}")
        return texts
    
    def _extract_texts_from_easyocr_result(self, result):
        """浠嶦asyOCR缁撴灉涓彁鍙栨枃鏈?""
        texts = []
        try:
            # EasyOCR杩斿洖鏍煎紡锛歔(bbox, text, confidence), ...]
            for detection in result:
                if len(detection) >= 2:
                    text = detection[1].strip()  # detection[1]鏄瘑鍒殑鏂囨湰
                    if text:
                        texts.append(text)
            
            print(f"EasyOCR璇嗗埆鍒皗len(texts)}鏉℃枃鏈?)
            return texts
            
        except Exception as e:
            print(f"EasyOCR鏂囨湰鎻愬彇鍑洪敊: {e}")
            return []
    
    def _contains_invoice_keywords(self, text):
        """妫€鏌ユ枃鏈槸鍚﹀寘鍚彂绁ㄥ叧閿瘝"""
        keywords = ['鍙戠エ', '澧炲€肩◣', '涓撶敤鍙戠エ', '鏅€氬彂绁?, '鍙戠エ鍙风爜', '鍙戠エ浠ｇ爜']
        return any(keyword in text for keyword in keywords)
    
    def _extract_invoice_info(self, text, image_path):
        """浠庢枃鏈腑鎻愬彇鍙戠エ淇℃伅"""
        company_name = ''
        invoice_number = ''
        invoice_date = ''
        invoice_amount = ''
        project_name = ''  # 鏂板椤圭洰鍚嶇О瀛楁
        
        print(f"鎻愬彇淇℃伅鐨勬枃鏈? {text}")
        
        try:
            # 鎻愬彇寮€绁ㄥ叕鍙稿悕绉?- 鏇寸伒娲荤殑鍖归厤鏂瑰紡
            company_patterns = [
                r'閿€鍞柟鍚嶇О[锛?]\s*([^\n\r銆愩€慮{2,100}?)(?=\s*銆恷$)',
                r'閿€鍞柟[锛?]\s*([^\n\r銆愩€慮{2,100}?)(?=\s*銆恷$)',
                r'寮€绁ㄦ柟鍚嶇О[锛?]\s*([^\n\r銆愩€慮{2,100}?)(?=\s*銆恷$)',
                r'寮€绁ㄦ柟[锛?]\s*([^\n\r銆愩€慮{2,100}?)(?=\s*銆恷$)',
                r'閿€鍞崟浣峓锛?]\s*([^\n\r銆愩€慮{2,100}?)(?=\s*銆恷$)',
                r'鏀舵鍗曚綅[锛?]\s*([^\n\r銆愩€慮{2,100}?)(?=\s*銆恷$)',
            ]
            
            for pattern in company_patterns:
                company_matches = re.findall(pattern, text)
                if company_matches:
                    for match in company_matches:
                        match = match.strip()
                        # 娓呯悊鍙兘鐨勫墠缂€
                        match = re.sub(r'^[閿€鍞紑绁ㄦ敹娆綸鏂筟鍚嶇О鍗曚綅]*[锛?]', '', match).strip()
                        # 鏇村鏉剧殑楠岃瘉鏉′欢
                        if (len(match) >= 2 and not match[0].isdigit() and 
                            not any(word in match for word in ['鍙戠エ', '鍙风爜', '鏃ユ湡', '閲戦', '椤圭洰'])):
                            company_name = match
                            print(f"鎻愬彇鍒板紑绁ㄥ叕鍙稿悕绉? {company_name}")
                            break
                    if company_name:
                        break
            
            # 濡傛灉涓婅堪妯″紡鏈尮閰嶅埌锛屽皾璇曟洿瀹芥澗鐨勬ā寮?
            if not company_name:
                # 灏濊瘯鍖归厤鍖呭惈"鍏徃"銆?鍘?銆?搴?绛夊叧閿瘝鐨勬枃鏈?
                company_loose_pattern = r'([^\n\r銆愩€慮{1,50}(?:鍏徃|鍘倈搴梶涓績|闆嗗洟|浼佷笟)[^\n\r銆愩€慮{0,30})'
                company_loose_matches = re.findall(company_loose_pattern, text)
                for match in company_loose_matches:
                    match = match.strip()
                    # 杩囨护鎺夋槑鏄句笉鏄叕鍙稿悕绉扮殑鍐呭
                    if (len(match) >= 3 and not match[0].isdigit() and 
                        not any(word in match for word in ['鍙戠エ', '鍙风爜', '鏃ユ湡', '閲戦', '椤圭洰', '璐拱鏂?, '涔版柟'])):
                        company_name = match
                        print(f"閫氳繃瀹芥澗妯″紡鎻愬彇鍒板紑绁ㄥ叕鍙稿悕绉? {company_name}")
                        break
        except Exception as e:
            print(f"寮€绁ㄥ叕鍙稿悕绉版彁鍙栧け璐? {e}")
        
        # 鏈€缁堟竻鐞嗗紑绁ㄥ叕鍙稿悕绉颁腑鐨?鍚嶇О锛?鍓嶇紑
        if company_name and company_name.startswith("鍚嶇О锛?):
            company_name = company_name[3:].strip()  # 鍘绘帀"鍚嶇О锛?鍓嶇紑
            print(f"娓呯悊鍓嶇紑鍚庣殑寮€绁ㄥ叕鍙稿悕绉? {company_name}")
        
        try:
            # 鎻愬彇鍙戠エ鍙风爜
            number_patterns = [
                r'鍙戠エ鍙风爜[锛?]銆?銆?([0-9]{6,20})',  # 澶勭悊銆愬彂绁ㄥ彿鐮侊細銆戙€愭暟瀛椼€戠殑鏍煎紡
                r'鍙戠エ鍙风爜[锛?]\s*([0-9]{6,20})',
                r'鍙戠エ鍙穂锛?]?\s*([0-9]{6,20})',
                r'鍙风爜[锛?]\s*([0-9]{6,20})',
                r'No[锛?.]?\s*([0-9]{6,20})',
                r'銆?[0-9]{15,20})銆?,  # 鐩存帴鍖归厤闀挎暟瀛楋紙鍙戠エ鍙风爜閫氬父寰堥暱锛?
            ]
            
            for pattern in number_patterns:
                number_matches = re.findall(pattern, text)
                if number_matches:
                    invoice_number = number_matches[0]
                    print(f"鎻愬彇鍒板彂绁ㄥ彿鐮? {invoice_number}")
                    break
        except Exception as e:
            print(f"鍙戠エ鍙风爜鎻愬彇澶辫触: {e}")
        
        try:
            # 鎻愬彇鍙戠エ鏃ユ湡 - 鏀寔澶氱鏍煎紡锛屼慨澶嶆棩鏈熼敊璇彁鍙栭噾棰濈殑闂
            date_patterns = [
                r'鍙戠エ鏃ユ湡[锛?]\s*([0-9]{4})骞?[0-9]{1,2})鏈?[0-9]{1,2})鏃?,  # YYYY骞碝M鏈圖D鏃?
                r'寮€绁ㄦ棩鏈焄锛?]\s*([0-9]{4})骞?[0-9]{1,2})鏈?[0-9]{1,2})鏃?,  # 寮€绁ㄦ棩鏈?
                r'鏃ユ湡[锛?]\s*([0-9]{4})骞?[0-9]{1,2})鏈?[0-9]{1,2})鏃?,      # 鏃ユ湡
                r'([0-9]{4})骞?[0-9]{1,2})鏈?[0-9]{1,2})鏃?,                 # 鐩存帴鏃ユ湡鏍煎紡
                r'鍙戠エ鏃ユ湡[锛?]\s*([0-9]{4})[.-]([0-9]{1,2})[.-]([0-9]{1,2})', # YYYY-MM-DD鎴朰YYY.MM.DD
                r'寮€绁ㄦ棩鏈焄锛?]\s*([0-9]{4})[.-]([0-9]{1,2})[.-]([0-9]{1,2})', # 寮€绁ㄦ棩鏈焂YYY-MM-DD
                r'([0-9]{4})[.-]([0-9]{1,2})[.-]([0-9]{1,2})',               # 鐩存帴YYYY-MM-DD鏍煎紡
            ]
            
            for pattern in date_patterns:
                date_matches = re.findall(pattern, text)
                if date_matches:
                    match = date_matches[0]
                    if isinstance(match, tuple) and len(match) >= 3:
                        year, month, day = match[0], match[1], match[2]
                    else:
                        # 濡傛灉鏄瓧绗︿覆鏍煎紡锛屽皾璇曞垎鍓?
                        date_str = match if isinstance(match, str) else str(match)
                        parts = re.split(r'[-骞存湀鏃?]', date_str)
                        if len(parts) >= 3:
                            year, month, day = parts[0], parts[1], parts[2]
                        else:
                            continue
                    
                    # 纭繚鏄湁鏁堢殑鏃ユ湡鏍煎紡
                    try:
                        year, month, day = int(year), int(month), int(day)
                        if 2000 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                            invoice_date = f"{year}{month:02d}{day:02d}"
                            print(f"鎻愬彇鍒板彂绁ㄦ棩鏈? {invoice_date}")
                            break
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            print(f"鍙戠エ鏃ユ湡鎻愬彇澶辫触: {e}")
        
        try:
            # 鎻愬彇鍙戠エ閲戦 - 浼樺厛鎻愬彇浠风◣鍚堣/瀹炰粯閲戦
            invoice_amount = ""
            
            # 绗竴浼樺厛绾э細浠风◣鍚堣鐩稿叧
            priority_patterns = [
                r'浠风◣鍚堣[锛?][^锟ヂd]*[锟ヂ?\s*([0-9]+\.?[0-9]*)',  # 浠风◣鍚堣锛?23.45
                r'浠风◣鍚堣[锛?][^锟ヂd]*([0-9]+\.?[0-9]*)\s*[锟ヂ?',  # 浠风◣鍚堣锛氾骏123.45
                r'瀹炰粯閲戦[锛?][^锟ヂd]*[锟ヂ?\s*([0-9]+\.?[0-9]*)',  # 瀹炰粯閲戦锛?23.45
                r'瀹炰粯[锛?][^锟ヂd]*[锟ヂ?\s*([0-9]+\.?[0-9]*)',     # 瀹炰粯锛?23.45
                r'搴斾粯閲戦[锛?][^锟ヂd]*[锟ヂ?\s*([0-9]+\.?[0-9]*)', # 搴斾粯閲戦锛?23.45
                r'鎬昏[锛?][^锟ヂd]*[锟ヂ?\s*([0-9]+\.?[0-9]*)',     # 鎬昏锛?23.45
                r'鎬婚噾棰漑锛?][^锟ヂd]*[锟ヂ?\s*([0-9]+\.?[0-9]*)',   # 鎬婚噾棰濓細123.45
            ]
            
            # 灏濊瘯绗竴浼樺厛绾фā寮?
            for pattern in priority_patterns:
                amount_matches = re.findall(pattern, text)
                if amount_matches:
                    valid_amounts = []
                    for amount_str in amount_matches:
                        try:
                            amount = float(amount_str)
                            # 杩囨护鎺夊彲鑳界殑閿欒鍖归厤锛堟瘮濡傛棩鏈熸暟瀛楋級
                            if amount >= 0.01 and amount <= 999999999:  # 闄愬埗鍚堢悊鑼冨洿
                                valid_amounts.append(amount)
                        except ValueError:
                            continue
                    
                    if valid_amounts:
                        invoice_amount = max(valid_amounts)  # 鍙栨渶澶х殑閲戦浣滀负鍙戠エ鎬婚
                        print(f"閫氳繃浼樺厛妯″紡鎻愬彇鍒板彂绁ㄩ噾棰? {invoice_amount} (妯″紡: {pattern})")
                        break
            
            # 绗簩浼樺厛绾э細濡傛灉娌℃湁鎵惧埌浠风◣鍚堣锛屽皾璇曞叾浠栨ā寮?
            if not invoice_amount:
                secondary_patterns = [
                    r'鍚堣[锛?][^锟ヂd]*[锟ヂ?\s*([0-9]+\.?[0-9]*)',     # 鍚堣锛?23.45
                    r'灏忓啓[锛?][^锟ヂd]*[锟ヂ?\s*([0-9]+\.?[0-9]*)',     # 灏忓啓锛?23.45
                    r'閲戦[锛圽(]鍚◣[锛塡)][锛?][^锟ヂd]*[锟ヂ?\s*([0-9]+\.?[0-9]*)', # 閲戦锛堝惈绋庯級锛?23.45
                ]
                
                for pattern in secondary_patterns:
                    amount_matches = re.findall(pattern, text)
                    if amount_matches:
                        valid_amounts = []
                        for amount_str in amount_matches:
                            try:
                                amount = float(amount_str)
                                if amount >= 0.01 and amount <= 999999999:
                                    valid_amounts.append(amount)
                            except ValueError:
                                continue
                        
                        if valid_amounts:
                            invoice_amount = max(valid_amounts)
                            print(f"閫氳繃娆¤妯″紡鎻愬彇鍒板彂绁ㄩ噾棰? {invoice_amount} (妯″紡: {pattern})")
                            break
            
            # 绗笁浼樺厛绾э細閫氱敤閲戦妯″紡锛堟渶鍚庡鐢級
            if not invoice_amount:
                fallback_patterns = [
                    r'[锟ヂ\s*([0-9]+\.?[0-9]*)',  # 锟?23.45
                ]
                
                for pattern in fallback_patterns:
                    amount_matches = re.findall(pattern, text)
                    if amount_matches:
                        # 瀵逛簬閫氱敤妯″紡锛屽彇鏈€鍚庝竴涓紙閫氬父鏄环绋庡悎璁★級
                        try:
                            amount = float(amount_matches[-1])  # 鍙栨渶鍚庝竴涓噾棰?
                            if amount >= 0.01 and amount <= 999999999:
                                invoice_amount = amount
                                print(f"閫氳繃澶囩敤妯″紡鎻愬彇鍒板彂绁ㄩ噾棰? {invoice_amount} (鏈€鍚庝竴涓噾棰?")
                                break
                        except ValueError:
                            continue
        except Exception as e:
            print(f"鍙戠エ閲戦鎻愬彇澶辫触: {e}")
        
        try:
            # 鎻愬彇椤圭洰鍚嶇О - 鏍规嵁鐢ㄦ埛鎻忚堪鏍煎紡銆?浣撹偛鐢ㄥ搧*Keep鍔ㄦ劅鍗曡溅銆?
            # 鍖归厤鍖呭惈*鐨勯」鐩悕绉版牸寮?
            project_patterns = [
                r'銆怽*([^\*銆慮+)\*([^\*銆慮+)銆?,  # 鏍煎紡濡傘€?浣撹偛鐢ㄥ搧*Keep鍔ㄦ劅鍗曡溅銆?
                r'椤圭洰鍚嶇О[锛?]\s*([^\n\r銆愩€慮+?)(?=\s*銆恷$)',
                r'椤圭洰[锛?]\s*([^\n\r銆愩€慮+?)(?=\s*銆恷$)',
                r'鍟嗗搧鍚嶇О[锛?]\s*([^\n\r銆愩€慮+?)(?=\s*銆恷$)',
                r'鍚嶇О[锛?]\s*([^\n\r銆愩€慮+?)(?=\s*銆恷$)',
                r'鏈嶅姟鍚嶇О[锛?]\s*([^\n\r銆愩€慮+?)(?=\s*銆恷$)',
                r'璐圭敤鍚嶇О[锛?]\s*([^\n\r銆愩€慮+?)(?=\s*銆恷$)',
            ]
            
            for pattern in project_patterns:
                project_matches = re.findall(pattern, text)
                print(f"椤圭洰鍚嶇О妯″紡 '{pattern}' 鍖归厤缁撴灉: {project_matches}")
                if project_matches:
                    if isinstance(project_matches[0], tuple) and len(project_matches[0]) >= 2:
                        # 瀵逛簬銆?浣撹偛鐢ㄥ搧*Keep鍔ㄦ劅鍗曡溅銆戞牸寮忥紝鍙栫浜岄儴鍒嗕綔涓洪」鐩悕绉?
                        project_name = project_matches[0][1].strip()
                    else:
                        project_name = project_matches[0].strip() if isinstance(project_matches[0], str) else str(project_matches[0]).strip()
                    
                    # 娓呯悊椤圭洰鍚嶇О
                    project_name = re.sub(r'[銆愩€慭*]', '', project_name).strip()
                    if project_name and len(project_name) > 1:
                        print(f"鎻愬彇鍒伴」鐩悕绉? {project_name}")
                        break
                    else:
                        project_name = ''
        except Exception as e:
            print(f"椤圭洰鍚嶇О鎻愬彇澶辫触: {e}")
        
        result = [image_path, company_name, invoice_number, invoice_date, invoice_amount, project_name]
        print(f"鏈€缁堟彁鍙栫粨鏋? {result}")
        return result

    def get_model_info(self):
        """鑾峰彇褰撳墠浣跨敤鐨勬ā鍨嬩俊鎭?""
        info = {
            "precision_mode": self.precision_mode,
            "offline_mode": self.offline_config is not None,
            "initialized": self.ocr_engine is not None
        }
        
        if self.offline_config:
            info["models_path"] = self.offline_config.get("models_path", "")
            info["available_models"] = list(self.offline_config.get("models", {}).keys())
            
            # 妫€鏌ユā鍨嬬姸鎬?
            models_available, message = self.check_models_available()
            info["models_status"] = message
            info["models_available"] = models_available
        
        return info

# 淇濇寔鍚戝悗鍏煎鎬?
OCRInvoice = OfflineOCRInvoice

if __name__ == '__main__':
    # 娴嬭瘯浠ｇ爜
    print("=" * 60)
    print("绂荤嚎OCR鍙戠エ璇嗗埆鍣ㄦ祴璇?(澶栭儴妯″瀷鏋舵瀯)")
    print("=" * 60)
    
    ocr_invoice = OfflineOCRInvoice()
    
    # 鏄剧ず妯″瀷淇℃伅
    model_info = ocr_invoice.get_model_info()
    print("妯″瀷淇℃伅:")
    for key, value in model_info.items():
        print(f"  {key}: {value}")
    
    # 妫€鏌ユā鍨嬪彲鐢ㄦ€?
    models_available, message = ocr_invoice.check_models_available()
    print(f"\n妯″瀷鐘舵€? {message}")
    
    if models_available:
        print("\n[OK] 妯″瀷鏂囦欢妫€鏌ラ€氳繃锛屽彲浠ヨ繘琛孫CR璇嗗埆")
        # 杩欓噷鍙互娣诲姞瀹為檯鐨勫浘鐗囨祴璇?
    else:
        print("\n[ERROR] 妯″瀷鏂囦欢缂哄け锛岃浣跨敤妯″瀷绠＄悊鍣ㄩ厤缃ā鍨嬫枃浠?)
        # EasyOCR 宸茬Щ闄わ紝鍏煎淇濈暀锛氶€€鍑虹▼搴?        return []


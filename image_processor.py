import os
import random
import string
from PIL import Image, ImageEnhance
import pandas as pd
from datetime import datetime

# ==========================================
# 설정값 (여기만 수정해서 쓰세요)
# ==========================================
INPUT_FOLDER = './raw_images'      # 원본 이미지가 있는 폴더
OUTPUT_FOLDER = './clean_images'   # 가공된 이미지가 저장될 폴더
KEYWORDS = [                       # 파일명 및 ALT 태그에 쓸 키워드 리스트
    "겨울철난방비절약", "보일러청소", "단열뽁뽁이", "가스비절약팁", 
    "겨울실내온도", "난방텐트추천", "웃풍차단", "창문틈새막기"
]
TARGET_WIDTH = 1000                # 리사이징 할 가로 크기
# ==========================================

def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_random_string(length=4):
    """파일명 중복 방지를 위한 랜덤 문자열 생성"""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def process_image(image_path, save_path):
    """이미지 세탁 (메타삭제 + 랜덤크롭 + 랜덤필터)"""
    try:
        img = Image.open(image_path)
        
        # 0. 극약처방: 로드 직후 즉시 리사이징 (메모리 폭발 방지)
        # 원본이 1500px보다 크다면, 아예 처음부터 줄여버림
        # LANCZOS 대신 BOX(또는 BILINEAR)를 써야 메모리 피크를 막음
        img.thumbnail((1500, 1500), Image.Resampling.BOX)
        
        # 1. RGBA(투명배경)인 경우 RGB로 변환 (JPG 저장을 위해)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # 2. 랜덤 크롭 (상하좌우 미세하게 잘라내기)
        w, h = img.size
        
        # 이미지가 너무 작을 경우 크롭 범위 조절
        crop_margin = 10
        if w <= 50 or h <= 50: 
            crop_margin = 0
            
        left = random.randint(0, crop_margin)
        top = random.randint(0, crop_margin)
        right = w - random.randint(0, crop_margin)
        bottom = h - random.randint(0, crop_margin)
        
        # 크롭 영역이 유효한지 확인
        if right > left and bottom > top:
            img = img.crop((left, top, right, bottom))

        # 3. 미세 필터 적용 (밝기, 대비, 채도를 랜덤하게 ±10% 조절)
        # 밝기
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(random.uniform(0.9, 1.1)) 
        # 대비
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(random.uniform(0.9, 1.1))
        
        # 4. 리사이징 (가로폭 고정, 비율 유지)
        if img.size[0] > 0:
            ratio = TARGET_WIDTH / float(img.size[0])
            h_size = int((float(img.size[1]) * float(ratio)))
            img = img.resize((TARGET_WIDTH, h_size), Image.Resampling.BOX)

        # 5. 저장 (메타데이터는 이 과정에서 자연스럽게 사라짐)
        img.save(save_path, quality=95)
        return True
        
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return False

def main():
    create_directory(INPUT_FOLDER) # 원본 폴더가 없으면 생성해둠
    create_directory(OUTPUT_FOLDER)
    
    # 원본 파일 목록 가져오기
    file_list = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    
    if not file_list:
        print(f"'{INPUT_FOLDER}' 폴더에 이미지가 없습니다. 이미지를 넣고 다시 실행해주세요.")
        return

    report_data = [] # 엑셀 저장을 위한 리스트

    print(f"총 {len(file_list)}개의 이미지 세탁을 시작합니다...")

    for i, filename in enumerate(file_list):
        # 사용할 키워드 순차 선택 (키워드가 부족하면 반복)
        keyword = KEYWORDS[i % len(KEYWORDS)]
        
        # 새 파일명 생성: 키워드_랜덤문자.jpg
        new_filename = f"{keyword}_{get_random_string()}.jpg"
        
        src_path = os.path.join(INPUT_FOLDER, filename)
        dst_path = os.path.join(OUTPUT_FOLDER, new_filename)
        
        # 이미지 처리 실행
        if process_image(src_path, dst_path):
            # 성공 시 리포트 데이터 추가
            alt_text = f"{keyword} 관련 이미지 자료" # ALT 태그 자동 생성 규칙
            report_data.append({
                '원본파일': filename,
                '세탁된파일': new_filename,
                '키워드': keyword,
                '추천_ALT태그': alt_text
            })

    # 엑셀 파일로 매핑 정보 저장 (추후 포스팅 봇이 이 파일을 읽어서 ALT 태그 입력)
    if report_data:
        df = pd.DataFrame(report_data)
        excel_path = os.path.join(OUTPUT_FOLDER, 'image_mapping_list.xlsx')
        df.to_excel(excel_path, index=False)
        
        print(f"\n작업 완료! {len(report_data)}개의 이미지가 생성되었습니다.")
        print(f"결과 폴더: {OUTPUT_FOLDER}")
        print(f"매핑 엑셀: {excel_path}")
    else:
        print("\n처리에 성공한 이미지가 없습니다.")

if __name__ == "__main__":
    main()

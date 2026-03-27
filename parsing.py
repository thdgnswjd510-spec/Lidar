import pymysql
import json
import pandas as pd

# 1. MySQL DB 연결 설정
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='1234',
    database='rosdb',
    charset='utf8'
)
cursor = conn.cursor()

# 2. 데이터 불러오기
print("DB에서 데이터를 불러오는 중...")
cursor.execute("SELECT ranges, action FROM lidardata")
rows = cursor.fetchall()

# 3. 데이터 파싱
parsed_data = []

for row in rows:
    ranges_str = row[0]
    action = row[1]

    # JSON 문자열 -> 파이썬 리스트 변환 (360개 거리 값)
    ranges_list = json.loads(ranges_str)

    # 리스트 맨 끝에 주행 액션(문자열) 추가 (총 361개 요소)
    ranges_list.append(action)

    # 한 줄의 데이터를 전체 리스트에 담기
    parsed_data.append(ranges_list)

# 4. 데이터프레임(DataFrame) 생성
column_names = [f"range_{i}" for i in range(360)] + ['action']

print("데이터프레임으로 변환 중...")
df = pd.DataFrame(parsed_data, columns=column_names)

# 5. 결과 확인 및 저장
print("\n파싱 완료! 데이터프레임 미리보기:")
print(df.head())
print(f"\n데이터프레임 형태 (행, 열): {df.shape}")

# CSV 파일 저장
csv_filename = 'lidar_parsed_data.csv'
df.to_csv(csv_filename, index=False)
print(f"'{csv_filename}' 파일로 저장이 완료되었습니다.")

# 연결 종료
cursor.close()
conn.close()
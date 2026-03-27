import roslibpy
import time
import math


class TurtlePrinter:
    def __init__(self, host='192.168.0.130', port=9090):
        self.client = roslibpy.Ros(host=host, port=9090)
        self.client.run()

        # 1. 폰트 데이터 압축 (가독성을 높인 구조)
        self.FONT = {
            'A': [(0, 0), (1, 2), (2, 0), (1.5, 0.8), (0.5, 0.8)],
            'B': [(0, 0), (0, 2), (1.2, 1.8), (0, 1), (1.4, 0.8), (0, 0)],
            'C': [(1.8, 1.6), (1, 2), (0, 1), (1, 0), (1.8, 0.4)],
            'D': [(0, 0), (0, 2), (1.5, 1.8), (1.5, 0.2), (0, 0)],
            'E': [(1.8, 2), (0, 2), (0, 0), (1.8, 0), (0, 0), (0, 1), (1.5, 1)],
            'F': [(1.8, 2), (0, 2), (0, 0), (0, 1), (1.5, 1)],
            'G': [(1.8, 1.6), (1, 2), (0, 1), (1, 0), (1.8, 0), (1.8, 0.8), (1.2, 0.8)],
            'H': [(0, 0), (0, 2), (0, 1), (1.5, 1), (1.5, 2), (1.5, 0)],
            'I': [(0.5, 2), (1.5, 2), (1, 2), (1, 0), (0.5, 0), (1.5, 0)],
            'J': [(0, 2), (2, 2), (1, 2), (1, 0.3), (0.5, 0), (0, 0.3)],
            'K': [(0, 0), (0, 2), (0, 1), (1.5, 2), (0, 1), (1.5, 0)],
            'L': [(0, 2), (0, 0), (1.8, 0)],
            'M': [(0, 0), (0, 2), (1, 1), (2, 2), (2, 0)],
            'N': [(0, 0), (0, 2), (1.8, 0), (1.8, 2)],
            'O': [(1, 2), (0, 1), (1, 0), (2, 1), (1, 2)],
            'P': [(0, 0), (0, 2), (1.5, 1.8), (0, 1)],
            'Q': [(1, 2), (0, 1), (1, 0), (2, 1), (1, 2), (1.3, 0.7), (2, 0)],
            'R': [(0, 0), (0, 2), (1.5, 1.8), (0, 1), (1.5, 0)],
            'S': [(1.8, 1.8), (1, 2), (0, 1.5), (1.8, 0.5), (1, 0), (0, 0.2)],
            'T': [(0, 2), (2, 2), (1, 2), (1, 0)],
            'U': [(0, 2), (0, 0.3), (1, 0), (2, 0.3), (2, 2)],
            'V': [(0, 2), (1, 0), (2, 2)],
            'W': [(0, 2), (0.5, 0), (1, 1), (1.5, 0), (2, 2)],
            'X': [(0, 2), (2, 0), (1, 1), (0, 0), (2, 2)],
            'Y': [(0, 2), (1, 1), (2, 2), (1, 1), (1, 0)],
            'Z': [(0, 2), (2, 2), (0, 0), (2, 0)]
        }

        # 관리용 리스트
        self.active_turtles = []

    def clear_screen(self):
        """기존에 생성된 모든 거북이 제거 및 화면 초기화"""
        kill_service = roslibpy.Service(self.client, '/kill', 'turtlesim/srv/Kill')

        # 1. 관리 리스트에 있는 거북이들 제거
        for name in self.active_turtles:
            try:
                kill_service.call(roslibpy.ServiceRequest({'name': name}))
            except:
                pass

        # 2. 혹시 모를 잔여 거북이 초기화 (리셋 서비스 호출 가능)
        reset_service = roslibpy.Service(self.client, '/reset', 'std_srvs/srv/Empty')
        reset_service.call(roslibpy.ServiceRequest())

        self.active_turtles = []
        print("화면을 초기화했습니다.")
        time.sleep(0.5)

    def draw_text(self, text):
        self.clear_screen()

        spawn_service = roslibpy.Service(self.client, '/spawn', 'turtlesim/srv/Spawn')

        X_START, Y_START = 1.0, 8.0
        X_GAP, Y_GAP = 2.5, 3.5
        CHARS_PER_LINE = 4
        STEPS = 12  # 부드러운 속도 조절

        text = text.upper().replace(" ", "")

        for i, char in enumerate(text):
            if char not in self.FONT: continue

            line, col = i // CHARS_PER_LINE, i % CHARS_PER_LINE
            curr_x, curr_y = X_START + (col * X_GAP), Y_START - (line * Y_GAP)

            # 거북이 소환
            pts = self.FONT[char]
            name = f"pro_{i}_{char}"
            self.active_turtles.append(name)

            spawn_req = roslibpy.ServiceRequest({
                'x': pts[0][0] + curr_x, 'y': pts[0][1] + curr_y,
                'theta': 0.0, 'name': name
            })
            spawn_service.call(spawn_req)

            teleport = roslibpy.Service(self.client, f'/{name}/teleport_absolute', 'turtlesim/srv/TeleportAbsolute')

            print(f"[{char}] 출력 중...")
            for p_idx in range(len(pts) - 1):
                s_p, e_p = pts[p_idx], pts[p_idx + 1]
                for step in range(1, STEPS + 1):
                    ratio = step / STEPS
                    ix = s_p[0] + (e_p[0] - s_p[0]) * ratio + curr_x
                    iy = s_p[1] + (e_p[1] - s_p[1]) * ratio + curr_y
                    teleport.call(roslibpy.ServiceRequest({'x': ix, 'y': iy, 'theta': 0.0}))
                    time.sleep(0.02)

    def run_forever(self):
        """사용자가 종료할 때까지 반복 입력 받는 루프"""
        print("\n=== 거북이 텍스트 프린터 시스템 ===")
        print("종료하려면 'exit' 또는 'Ctrl+C'를 입력하세요.")

        try:
            while True:
                user_input = input("\n출력할 영문 입력: ").strip()
                if user_input.lower() == 'exit':
                    break
                if not user_input:
                    continue

                self.draw_text(user_input)
                print("출력 완료!")
        except KeyboardInterrupt:
            pass
        finally:
            self.client.terminate()
            print("\n시스템을 종료합니다.")


# 메인 실행
if __name__ == "__main__":
    printer = TurtlePrinter()
    printer.run_forever()
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import threading
import whisper
import google.generativeai as genai
import os
import sys
import webbrowser
from datetime import datetime

def resource_path(relative_path):
    """실행 파일로 묶였을 때 내부의 임시 폴더 경로를 찾아주는 함수"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 시스템 환경 변수(PATH)의 맨 앞에 내장된 FFmpeg 경로를 몰래 끼워 넣습니다.
os.environ["PATH"] = resource_path("") + os.pathsep + os.environ.get("PATH", "")

# --- 개발자용 터미널 전용 로깅 함수 ---
def dev_log(msg):
    """GUI 텍스트박스가 아닌, 실제 터미널(콘솔)에만 로그를 강제로 출력합니다."""
    # 터미널 창(--noconsole)이 없어서 stdout이 None인 경우 에러를 방지합니다.
    if sys.__stdout__ is not None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        sys.__stdout__.write(f"[{timestamp}] [DEV] {msg}\n")
        sys.__stdout__.flush()

whisper_model = None

# --- 실시간 터미널 출력(stdout)을 텍스트창으로 빼돌리는 클래스 ---
class TextRedirector(object):
    def __init__(self, widget):
        self.widget = widget

    def write(self, str_data):
        self.widget.insert("end", str_data)
        self.widget.see("end")

    def flush(self):
        pass

# --- 빙빙 도는 링(Spinner) 애니메이션 클래스 ---
class LoadingRing:
    def __init__(self, label_widget):
        self.label = label_widget
        self.frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.index = 0
        self.is_spinning = False

    def spin(self):
        if self.is_spinning:
            self.label.configure(text=self.frames[self.index])
            self.index = (self.index + 1) % len(self.frames)
            self.label.after(80, self.spin)

    def start(self):
        self.is_spinning = True
        self.spin()

    def stop(self, final_icon="✅"):
        self.is_spinning = False
        self.label.configure(text=final_icon)


# CustomTkinter + Drag & Drop 래퍼 클래스
class TkinterDnD_CTk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


class STTApp(TkinterDnD_CTk):
    def __init__(self):
        super().__init__()

        self.title("AI 음성 기록 & 교정기")
        self.geometry("850x750")
        self.minsize(800, 600)
        
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.audio_file_path = ""
        self.show_adv = False 

        self.font_main = ("맑은 고딕", 14)
        self.font_bold = ("맑은 고딕", 15, "bold")
        self.font_title = ("맑은 고딕", 16, "bold")

        # --- 화면 레이아웃 구성 ---
        
        # 0. API 키 입력 영역 (사용자 직접 입력 방식 - BYOK)
        self.frame_api = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_api.pack(pady=(20, 0), padx=20, fill="x")
        
        self.lbl_api = ctk.CTkLabel(self.frame_api, text="🔑 Gemini API 키:", font=self.font_bold)
        self.lbl_api.pack(side="left", padx=(0, 10))
        
        self.entry_api = ctk.CTkEntry(self.frame_api, width=350, show="*", font=self.font_main, placeholder_text="발급받은 API 키를 입력하세요")
        self.entry_api.pack(side="left", padx=10)
        
        self.btn_api_guide = ctk.CTkButton(self.frame_api, text="무료 발급받기", width=100, font=self.font_main,
                                           command=lambda: webbrowser.open("https://aistudio.google.com/"))
        self.btn_api_guide.pack(side="left", padx=10)

        # 1. 드래그 앤 드롭 영역
        self.frame_drop = ctk.CTkFrame(self, corner_radius=15, fg_color=("gray80", "gray20"))
        self.frame_drop.pack(pady=(15, 10), padx=20, fill="x")
        
        self.lbl_drop = ctk.CTkLabel(self.frame_drop, text="📁 이곳에 음성 파일(.mp3, .m4a, .wav)을 끌어다 놓으세요\n또는 클릭해서 파일을 선택하세요.", font=self.font_main)
        self.lbl_drop.pack(pady=20)
        
        self.frame_drop.bind("<Button-1>", lambda e: self.select_file_dialog())
        self.lbl_drop.bind("<Button-1>", lambda e: self.select_file_dialog())
        self.frame_drop.drop_target_register(DND_FILES)
        self.frame_drop.dnd_bind('<<Drop>>', self.drop_file)

        # 2. 상세 설정 영역
        self.btn_toggle = ctk.CTkButton(self, text="▶ 상세 설정 열기 (맥락 및 핵심 키워드 입력)", 
                                        font=self.font_main, fg_color="transparent", text_color=("gray10", "gray90"), 
                                        hover_color=("gray70", "gray30"), anchor="w", 
                                        command=self.toggle_adv)
        self.btn_toggle.pack(pady=0, padx=20, fill="x")

        self.frame_mid = ctk.CTkFrame(self)
        
        self.lbl_context = ctk.CTkLabel(self.frame_mid, text="맥락 (예: 회의, 강의):", font=self.font_main)
        self.lbl_context.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.entry_context = ctk.CTkEntry(self.frame_mid, width=600, font=self.font_main)
        self.entry_context.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.lbl_keywords = ctk.CTkLabel(self.frame_mid, text="핵심 키워드:", font=self.font_main)
        self.lbl_keywords.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.entry_keywords = ctk.CTkEntry(self.frame_mid, width=600, font=self.font_main)
        self.entry_keywords.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # 3. 진행 상태 표시 영역
        self.frame_progress = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_progress.pack(pady=(10, 5), padx=20, fill="x")
        
        self.lbl_ring = ctk.CTkLabel(self.frame_progress, text="⏸", font=("맑은 고딕", 24, "bold"), text_color="#3B8ED0")
        self.lbl_ring.pack(side="left", padx=(10, 10))
        
        self.lbl_status = ctk.CTkLabel(self.frame_progress, text="대기 중...", font=self.font_bold)
        self.lbl_status.pack(side="left")

        self.spinner = LoadingRing(self.lbl_ring)

        # 4. 실행 버튼
        self.btn_start = ctk.CTkButton(self, text="▶ 변환 및 교정 시작", command=self.start_process, height=45, font=self.font_title)
        self.btn_start.pack(pady=(5, 15))

        # 5. 다운로드 버튼
        self.btn_save = ctk.CTkButton(self, text="💾 다운로드", command=self.save_text, height=45, fg_color="#28a745", hover_color="#218838", font=self.font_title)
        self.btn_save.pack(side="bottom", pady=(10, 20))

        # 6. 결과 출력 텍스트 박스
        self.textbox_result = ctk.CTkTextbox(self, width=800, font=self.font_main)
        self.textbox_result.pack(side="top", pady=0, padx=20, fill="both", expand=True)
        
        dev_log("GUI 애플리케이션 초기화 완료")

    # --- 기능 함수 구현 ---
    
    def toggle_adv(self):
        self.show_adv = not self.show_adv
        if self.show_adv:
            self.btn_toggle.configure(text="▼ 상세 설정 닫기 (맥락 및 핵심 키워드 입력)")
            self.frame_mid.pack(after=self.btn_toggle, pady=5, padx=20, fill="x")
            dev_log("상세 설정 UI 펼침")
        else:
            self.btn_toggle.configure(text="▶ 상세 설정 열기 (맥락 및 핵심 키워드 입력)")
            self.frame_mid.pack_forget()
            dev_log("상세 설정 UI 접음")

    def select_file_dialog(self):
        filetypes = (("Audio files", "*.mp3 *.m4a *.wav"), ("All files", "*.*"))
        path = filedialog.askopenfilename(title="음성 파일 선택", filetypes=filetypes)
        if path:
            self.set_file_path(path)

    def drop_file(self, event):
        path = event.data.strip('{}')
        self.set_file_path(path)
        
    def set_file_path(self, path):
        self.audio_file_path = path
        filename = os.path.basename(path)
        self.lbl_drop.configure(text=f"✅ 선택된 파일: {filename}\n(클릭하여 다른 파일로 변경)")
        dev_log(f"음성 파일 로드됨: {path}")

    def start_process(self):
        # API 키 입력 확인 로직 추가
        user_api_key = self.entry_api.get().strip()
        if not user_api_key:
            messagebox.showwarning("경고", "Gemini API 키를 먼저 입력해주세요!")
            return
            
        if not self.audio_file_path:
            messagebox.showwarning("경고", "음성 파일을 먼저 선택하거나 끌어다 놓아주세요!")
            return
            
        context = self.entry_context.get()
        keywords = self.entry_keywords.get()
        
        self.btn_start.configure(state="disabled")
        self.textbox_result.delete("0.0", "end")
        
        dev_log("--- 파이프라인 스레드 시작 ---")
        threading.Thread(target=self.run_ai_pipeline, args=(context, keywords, user_api_key), daemon=True).start()

    def run_ai_pipeline(self, context, keywords, api_key):
        global whisper_model
        
        # 사용자가 입력한 API 키로 Gemini 설정 적용
        try:
            genai.configure(api_key=api_key)
            llm_model = genai.GenerativeModel('gemini-2.5-flash')
            dev_log("Gemini API 설정 완료 (사용자 입력 키 적용)")
        except Exception as e:
            dev_log(f"API 설정 오류: {e}")
            messagebox.showerror("오류", "API 키 설정 중 문제가 발생했습니다. 키를 다시 확인해주세요.")
            self.btn_start.configure(state="normal")
            return
        
        old_stdout = sys.stdout
        sys.stdout = TextRedirector(self.textbox_result)
        
        try:
            self.spinner.start()
            self.lbl_status.configure(text="1차 작업 중: 음성을 텍스트로 추출하고 있습니다... ⏳")
            
            # 1. Whisper 변환 단계
            dev_log("1차 STT (Whisper) 단계 진입")
            if whisper_model is None:
                dev_log("Whisper Small 모델 메모리 로딩 시작 (최초 1회)")
                print("[시스템] 최초 실행입니다. Whisper AI 모델을 로딩합니다...\n")
                whisper_model = whisper.load_model("small")
                dev_log("Whisper 모델 로딩 완료")
            
            dev_log(f"Whisper 변환 시작 (대상: {os.path.basename(self.audio_file_path)})")
            print("=== [1차 변환 실시간 로그 (Whisper)] ===")
            
            result = whisper_model.transcribe(self.audio_file_path, language="ko", verbose=True)
            raw_text = result["text"]
            print("\n")
            
            sys.stdout = old_stdout
            dev_log(f"1차 STT 완료. 추출된 원문 길이: {len(raw_text)}자")
            
            # 2. Gemini 교정 단계
            self.lbl_status.configure(text="2차 작업 중: 제미나이가 문맥에 맞게 텍스트를 분석하고 교정 중입니다... ⏳")
            dev_log("2차 LLM 교정 단계 진입")
            dev_log(f"전달할 맥락(Context): '{context if context else '없음'}'")
            dev_log(f"전달할 키워드(Keywords): '{keywords if keywords else '없음'}'")
            
            prompt = f"""
            당신은 전문적인 텍스트 교정 및 편집기입니다. 
            아래의 [원문 텍스트]를 [맥락]과 [핵심 키워드]를 참고하여 심층적으로 분석하고 교정해주세요.
            
            [절대 지시사항]
            1. 고유명사, 오탈자, 문법, 띄어쓰기를 완벽하게 교정하고 자연스러운 문장으로 다듬으세요.
            2. 내용의 흐름과 주제가 바뀌는 지점에 따라 적절히 단락(문단)을 나누고, 줄바꿈을 적용하여 가독성을 높이세요.
            3. 각 단락의 시작 부분에는 반드시 들여쓰기(스페이스바 4번)를 적용하세요.
            4. "다듬어진 텍스트입니다", "안녕하세요" 같은 인사말, 제목, 마크다운 기호(##, ** 등)나 부연 설명을 절대 포함하지 마세요.
            5. 오직 최종적으로 교정되고 포맷팅된 텍스트 결과물만 출력하세요.
            
            [맥락]: {context}
            [핵심 키워드]: {keywords}
            
            [원문 텍스트]:
            {raw_text}
            """
            
            self.textbox_result.insert("end", "=== [최종 교정 실시간 출력 (Gemini)] ===\n")
            dev_log("Gemini API 호출 및 스트리밍 응답 대기 중...")
            
            response = llm_model.generate_content(prompt, stream=True)
            for chunk in response:
                self.textbox_result.insert("end", chunk.text)
                self.textbox_result.see("end")
                
            dev_log("Gemini API 스트리밍 응답 수신 완료")
            
            self.spinner.stop("✅")
            self.lbl_status.configure(text="모든 변환 및 교정 작업이 완료되었습니다!")
            dev_log("--- 파이프라인 정상 종료 ---")
            
        except Exception as e:
            sys.stdout = old_stdout 
            self.spinner.stop("❌")
            self.lbl_status.configure(text="작업 중 오류가 발생했습니다.")
            dev_log(f"ERROR: 파이프라인 실행 중 예외 발생 - {str(e)}")
            messagebox.showerror("오류", f"작업 중 오류가 발생했습니다:\n{e}")
            
        finally:
            self.btn_start.configure(state="normal")
            
    def save_text(self):
        text_content = self.textbox_result.get("0.0", "end-1c")
        separator = "=== [최종 교정 실시간 출력 (Gemini)] ==="
        
        if separator in text_content:
            text_to_save = text_content.split(separator)[-1].strip()
        else:
            text_to_save = text_content.strip() 

        if not text_to_save:
            dev_log("다운로드 시도 실패: 저장할 텍스트가 없음")
            messagebox.showinfo("알림", "다운로드할 내용이 없습니다.")
            return
            
        if self.audio_file_path:
            original_filename = os.path.basename(self.audio_file_path)
            name_without_ext = os.path.splitext(original_filename)[0]
            initial_name = f"{name_without_ext}_text.txt"
        else:
            initial_name = "음성변환_결과_text.txt"
            
        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt", 
            filetypes=[("Text files", "*.txt")],
            title="텍스트 저장",
            initialfile=initial_name
        )
        
        if save_path:
            dev_log(f"파일 저장 진행: 경로={save_path}, 글자수={len(text_to_save)}자")
            credit_text = "\n\n---\nDeveloped by freeycfreeyc\nVisit my github to check more updates: https://github.com/freeycfreeyc"
            final_output = text_to_save + credit_text
            
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(final_output)
                dev_log("파일 저장 완료")
                messagebox.showinfo("저장 완료", "다운로드가 완료되었습니다.")
            except Exception as e:
                dev_log(f"ERROR: 파일 저장 실패 - {str(e)}")
                messagebox.showerror("오류", f"파일을 저장할 수 없습니다:\n{e}")

if __name__ == "__main__":
    app = STTApp()
    app.mainloop()
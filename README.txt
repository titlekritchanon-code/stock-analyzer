Stock Analyzer — รุ่นแก้ Failed to fetch

ต้องมี Python 3.10 ขึ้นไป ไม่ต้องติดตั้งแพ็กเกจหรือ API key
1. แตก ZIP
2. เปิด Terminal ในโฟลเดอร์ที่แตกไฟล์
3. ตั้งอีเมลติดต่อจริงสำหรับนโยบาย SEC (ไม่ใช่ API key):
   Windows PowerShell: $env:SEC_CONTACT_EMAIL="your-real-email@domain.com"
   macOS/Linux: export SEC_CONTACT_EMAIL="your-real-email@domain.com"
4. รัน: python server.py (macOS อาจใช้ python3 server.py)
5. เปิด http://localhost:8000
อย่าเปิด index.html โดยดับเบิลคลิก เพราะต้องผ่าน local server

เบราว์เซอร์เรียก backend ของตัวเอง จึงไม่เรียก SEC ข้าม origin โดยตรง
Backend ขอข้อมูลจาก SEC/Stooq โดยตั้ง timeout, cache 15 นาที และแสดงผลแยกส่วนเมื่อแหล่งใดล้มเหลว
SEC อาจปฏิเสธบาง IP ได้ แม้ตั้ง User-Agent แล้ว ไม่มีการรับประกัน uptime ของแหล่งข้อมูล
อีเมลติดต่อถูกส่งเป็น User-Agent ให้ SEC เท่านั้น ไม่ใช่รหัสผ่าน
ข้อมูลราคาเป็นราคาปิดตามวันที่ที่แสดง ไม่ใช่ราคาสด งบกำไรเป็นงบปี ไม่อ้างว่าเป็นไตรมาสล่าสุด
ไม่มีการทดสอบเชื่อมต่อ upstream หรือ browser end-to-end ในสภาพแวดล้อมที่สร้างไฟล์นี้

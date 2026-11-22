import json, os, shutil, subprocess, uuid, urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent
CLIPS=ROOT/'dados'/'clips'
CLIPS.mkdir(parents=True,exist_ok=True)
OLLAMA=os.getenv('OLLAMA_URL','http://127.0.0.1:11434').rstrip('/')
PORT=int(os.getenv('WMK_PORT','8767'))

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
    def answer(self,status,data):
        b=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def get_data(self,limit=20*1024*1024):
        n=int(self.headers.get('Content-Length','0'))
        if n>limit:raise ValueError('Conteúdo excessivo')
        return json.loads(self.rfile.read(n) or b'{}')
    def do_GET(self):
        if urlsplit(self.path).path=='/api/status':
            names=[];connected=False
            try:
                with urllib.request.urlopen(OLLAMA+'/api/tags',timeout=2) as r:
                    names=[m['name'] for m in json.load(r).get('models',[])]
                    connected=True
            except Exception:pass
            return self.answer(200,{'ok':True,'versao':'0.1.0','ollama':connected,'modelos':names,'ffmpeg':bool(shutil.which('ffmpeg'))})
        return super().do_GET()
    def do_PUT(self):
        if urlsplit(self.path).path!='/api/upload':return self.answer(404,{'erro':'Rota inválida'})
        n=int(self.headers.get('Content-Length','0'))
        if n<1 or n>300*1024*1024:return self.answer(413,{'erro':'Máximo 300MB'})
        if self.headers.get('Content-Type')!='video/mp4':return self.answer(415,{'erro':'Apenas MP4'})
        name=uuid.uuid4().hex+'.mp4'
        dest=CLIPS/name
        with dest.open('wb') as w:
            remaining=n
            while remaining:
                part=self.rfile.read(min(1024*1024,remaining))
                if not part:break
                w.write(part);remaining-=len(part)
        if remaining:
            dest.unlink(missing_ok=True)
            return self.answer(400,{'erro':'Upload incompleto'})
        return self.answer(200,{'arquivo':name,'url':'/dados/clips/'+name})
    def do_POST(self):
        try:
            data=self.get_data()
            path=urlsplit(self.path).path
            if path=='/api/prompt':
                model=str(data.get('modelo',''))
                idea=str(data.get('ideia',''))[:9000]
                if not model or not idea:return self.answer(400,{'erro':'Modelo e ideia obrigatórios'})
                prompt=('Você é diretor de cinema. Crie prompt cinematográfico em INGLÊS usando seções integrated_multimodal_description, overall_soundscape e non_diegetic_music. Descreva câmera, iluminação, cenário, ações, tempo e áudio; diálogos em português. Apenas o prompt. Ideia: '+idea)
                payload=json.dumps({'model':model,'messages':[{'role':'user','content':prompt}],'stream':False,'options':{'num_predict':900}}).encode()
                req=urllib.request.Request(OLLAMA+'/api/chat',payload,{'Content-Type':'application/json'},method='POST')
                try:
                    with urllib.request.urlopen(req,timeout=180) as r:
                        result=json.load(r)
                    return self.answer(200,{'prompt':result.get('message',{}).get('content','')})
                except Exception as e:return self.answer(502,{'erro':'Ollama: '+str(e)})
            if path=='/api/export':
                clips=data.get('clips',[])
                ffmpeg=shutil.which('ffmpeg')
                if not ffmpeg:return self.answer(400,{'erro':'FFmpeg não encontrado'})
                if not isinstance(clips,list) or not 0<len(clips)<=60:return self.answer(400,{'erro':'Nenhum clipe selecionado'})
                sources=[]
                for c in clips:
                    if not isinstance(c,str) or not c.endswith('.mp4') or '/' in c or '\\' in c:return self.answer(400,{'erro':'Clipe inválido'})
                    src=CLIPS/c
                    if not src.is_file():return self.answer(404,{'erro':'Clipe ausente'})
                    sources.append(src)
                export=ROOT/'dados'/'exportacoes'
                export.mkdir(exist_ok=True)
                dest=export/(uuid.uuid4().hex[:8]+'-filme.mp4')
                cmd=[ffmpeg,'-y','-hide_banner','-loglevel','error']
                for src in sources:cmd+=['-i',str(src)]
                filt=''.join(f'[{i}:v:0]fps=24,scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p,setpts=PTS-STARTPTS[v{i}];' for i in range(len(sources)))
                filt+=''.join(f'[v{i}]' for i in range(len(sources)))+f'concat=n={len(sources)}:v=1:a=0[outv]'
                cmd+=['-filter_complex',filt,'-map','[outv]','-c:v','libx264','-preset','veryfast','-crf','24','-movflags','+faststart',str(dest)]
                try:
                    r=subprocess.run(cmd,capture_output=True,text=True,timeout=300)
                    if r.returncode:return self.answer(500,{'erro':r.stderr[-1000:]})
                    return self.answer(200,{'arquivo':'/dados/exportacoes/'+dest.name,'aviso':'Exportação sem áudio nesta versão'})
                except subprocess.TimeoutExpired:return self.answer(504,{'erro':'Exportação excedeu tempo limite'})
            return self.answer(404,{'erro':'Rota desconhecida'})
        except Exception as e:return self.answer(400,{'erro':str(e)})

if __name__=='__main__':
    print('WMK MiniMax-H3 Lite v0.1 — http://127.0.0.1:'+str(PORT))
    ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()

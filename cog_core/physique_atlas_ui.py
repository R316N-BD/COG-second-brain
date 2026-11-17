"""Local anatomical mesh viewer and independent animated movement teaching lab."""
import math
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from .physique_atlas import PRESETS,ATTRIBUTION,load_region,normalize_mesh
from .physique_biomechanics import EXERCISES,frame
import zipfile

def mount_atlas(page):
    style="Physique.TLabel";fs="Physique.TFrame"
    ttk.Label(page,text="BODY PARTS 3D / Anatomical mesh viewer",style=style,font=("Segoe UI",16,"bold")).pack(anchor="w")
    ttk.Label(page,text="Select the official IS-A 4.0 ZIP and matching isa_element_parts.txt. Import one muscle group at a time. Source geometry is static and not an individual scan.",style=style,wraplength=920).pack(anchor="w")
    row=ttk.Frame(page,style=fs);row.pack(fill="x",pady=5)
    selection=tk.StringVar(value=next(iter(PRESETS)))
    ttk.Combobox(row,textvariable=selection,values=tuple(PRESETS),state="readonly",width=24).pack(side="left",padx=3)
    source={"zip":"","meta":"","mesh":None,"normalized":[],"pending":False,"drag":None}
    status=tk.StringVar(value="No anatomical assets imported.")
    def choose(key,types):
        path=filedialog.askopenfilename(parent=page.winfo_toplevel(),filetypes=types)
        if path:source[key]=path;status.set("Source selected; choose Import selected group.")
    ttk.Button(row,text="Choose ZIP",command=lambda:choose("zip",[("ZIP archive","*.zip")])).pack(side="left",padx=3)
    ttk.Button(row,text="Choose metadata",command=lambda:choose("meta",[("Metadata","*.txt")])).pack(side="left",padx=3)
    axis=tk.StringVar(value="z");sign=tk.IntVar(value=-1)
    ttk.Combobox(row,textvariable=axis,values=("z","y"),state="readonly",width=3).pack(side="left")
    ttk.Label(row,text="up",style=style).pack(side="left")
    ttk.Checkbutton(row,text="Flip front",variable=sign,onvalue=1,offvalue=-1).pack(side="left")
    canvas=tk.Canvas(page,bg="#101c2b",highlightthickness=0,height=380);canvas.pack(fill="both",expand=True)
    yaw=tk.DoubleVar(value=0);pitch=tk.DoubleVar(value=0);zoom=tk.DoubleVar(value=1)
    controls=ttk.Frame(page,style=fs);controls.pack(fill="x")
    for label,a in (("Front",0),("Side",90),("Back",180)):
        ttk.Button(controls,text=label,command=lambda x=a:(yaw.set(x),pitch.set(0))).pack(side="left",padx=2)
    ttk.Label(controls,text="Zoom",style=style).pack(side="left",padx=5)
    ttk.Scale(controls,from_=.5,to=2,variable=zoom).pack(side="left",fill="x",expand=True)
    ttk.Label(page,textvariable=status,style=style,wraplength=920).pack(anchor="w",pady=4)
    ttk.Label(page,text=ATTRIBUTION,style=style,wraplength=920).pack(anchor="w")
    def render():
        source["pending"]=False
        canvas.delete("all")
        w=max(canvas.winfo_width(),200);h=max(canvas.winfo_height(),200)
        if not source["normalized"]:
            canvas.create_text(w/2,h/2,text="Import an official muscle group",fill="#9db2ca");return
        a=math.radians(yaw.get());b=math.radians(pitch.get());ca=math.cos(a);sa=math.sin(a);cb=math.cos(b);sb=math.sin(b)
        scale=min(w,h)*.83*zoom.get()
        def rotate(p):
            x,y,z=p;x,z=x*ca+z*sa,-x*sa+z*ca
            return (x,y*cb-z*sb,y*sb+z*cb)
        polys=[]
        for i,(element,tris) in enumerate(source["normalized"]):
            for tri in tris:
                p=[rotate(v) for v in tri]
                u=[p[1][j]-p[0][j] for j in range(3)];v=[p[2][j]-p[0][j] for j in range(3)]
                n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                length=math.hypot(*n)
                if length<1e-12:continue
                # Two-sided shading; no assumption about imported winding.
                light=.42+.58*abs((n[2]-.35*n[0]-.15*n[1])/length)/1.08
                base=(181,97,89) if i%2==0 else (212,128,102)
                color="#"+ "".join(f"{min(255,int(x*light)):02x}" for x in base)
                coords=[v for x,y,z in p for v in (w/2+x*scale,h/2+y*scale)]
                polys.append((sum(p0[2] for p0 in p)/3,coords,color))
        for _,coords,color in sorted(polys,key=lambda p:p[0]):canvas.create_polygon(*coords,fill=color,outline="")
    def schedule(*_):
        if not source["pending"]:
            source["pending"]=True;canvas.after_idle(render)
    def transform(*_):
        if source["mesh"]:
            source["normalized"]=normalize_mesh(source["mesh"]["meshes"],axis.get(),sign.get())
            schedule()
    def import_group():
        try:
            if not source["zip"] or not source["meta"]:raise ValueError("Choose both official files.")
            new=load_region(source["zip"],source["meta"],PRESETS[selection.get()])
            normalized=normalize_mesh(new["meshes"],axis.get(),sign.get())
            source["mesh"]=new;source["normalized"]=normalized
            status.set("Imported "+", ".join(new["names"])+f" • {new['triangle_count']:,} triangles. Coordinates fitted to selected group. Metadata SHA-256: "+new["metadata_sha256"][:16]+"…")
            schedule()
        except (ValueError,OSError,zipfile.BadZipFile,RuntimeError) as exc:
            messagebox.showerror("Anatomical import",str(exc),parent=page.winfo_toplevel())
    ttk.Button(row,text="Import selected group",command=import_group).pack(side="left",padx=3)
    def press(e):source["drag"]=(e.x,e.y,yaw.get(),pitch.get())
    def move(e):
        d=source["drag"]
        if d:yaw.set((d[2]+(e.x-d[0])*.6)%360);pitch.set(max(-80,min(80,d[3]+(e.y-d[1])*.5)))
    canvas.bind("<ButtonPress-1>",press);canvas.bind("<B1-Motion>",move)
    canvas.bind("<ButtonRelease-1>",lambda e:source.update(drag=None))
    canvas.bind("<Configure>",schedule)
    for var in (yaw,pitch,zoom):var.trace_add("write",schedule)
    for var in (axis,sign):var.trace_add("write",transform)
    schedule()

def mount_movement(page):
    style="Physique.TLabel";fs="Physique.TFrame"
    ttk.Label(page,text="MOVEMENT LAB / Joint-angle animation",style=style,font=("Segoe UI",16,"bold")).pack(anchor="w")
    ttk.Label(page,text="Illustrative planar joint model; not animated BodyParts3D meshes, exercise instructions, medical advice or measured human motion.",style=style,wraplength=920).pack(anchor="w")
    controls=ttk.Frame(page,style=fs);controls.pack(fill="x",pady=6)
    exercise=tk.StringVar(value=next(iter(EXERCISES)));phase=tk.DoubleVar(value=0);speed=tk.DoubleVar(value=1)
    ttk.Combobox(controls,textvariable=exercise,values=tuple(EXERCISES),state="readonly",width=24).pack(side="left",padx=4)
    play=tk.BooleanVar(value=False)
    ttk.Checkbutton(controls,text="Play",variable=play).pack(side="left")
    ttk.Label(controls,text="Speed",style=style).pack(side="left",padx=5)
    ttk.Scale(controls,from_=.25,to=2,variable=speed).pack(side="left",fill="x",expand=True)
    canvas=tk.Canvas(page,bg="#101c2b",highlightthickness=0,height=380);canvas.pack(fill="both",expand=True)
    ttk.Scale(page,from_=0,to=1,variable=phase).pack(fill="x",pady=5)
    details=tk.StringVar()
    ttk.Label(page,textvariable=details,style=style,wraplength=900,justify="left").pack(anchor="w")
    bones=(("ankle","knee"),("knee","hip"),("hip","shoulder"),("shoulder","elbow"),("elbow","wrist"),("shoulder","head"))
    def draw(*_):
        data=frame(exercise.get(),phase.get());pts=data["points"];angles=data["angles"]
        w=max(canvas.winfo_width(),200);h=max(canvas.winfo_height(),200);scale=min(w*.55,h/2.4)
        def screen(p):return (w*.5+p[0]*scale,h*.22+p[1]*scale)
        canvas.delete("all")
        for a,b in bones:
            x,y=screen(pts[a]);xx,yy=screen(pts[b])
            canvas.create_line(x,y,xx,yy,fill="#36ddc7",width=8,capstyle="round")
        for key,p in pts.items():
            x,y=screen(p);r=13 if key=="head" else 5
            canvas.create_oval(x-r,y-r,x+r,y+r,fill="#dce7f4",outline="#101c2b")
        for key,value in angles.items():
            x,y=screen(pts[key]);canvas.create_text(x+14,y-9,text=f"{key} {value:.0f}°",fill="#cbd5e1",anchor="w")
        _,description,muscles=EXERCISES[exercise.get()]
        details.set(description+" • Related regions: "+", ".join(muscles)+"\nInterior joint angles, not prescribed ranges or anatomical activation. Phase "+f"{phase.get():.2f}")
    def tick():
        if not page.winfo_exists():return
        if play.get() and page.winfo_ismapped():phase.set((phase.get()+.008*speed.get())%1)
        page.after(40,tick)
    for v in (exercise,phase):v.trace_add("write",draw)
    canvas.bind("<Configure>",draw);draw();page.after(40,tick)

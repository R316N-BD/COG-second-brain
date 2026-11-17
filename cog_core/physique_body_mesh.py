"""Dependency-free polygonal teaching model. Original stylized geometry, not a scan."""
import math

# region, side, depth layer, center (x,y,z), radii, tilt about z in degrees.
# y increases downward; positive z faces the front. All dimensions arbitrary.
PARTS=[
 ("","center","base",(0,.42,0),(.115,.145,.10),0),
 ("","center","base",(0,.60,0),(.075,.09,.07),0),
 ("","center","base",(0,.88,0),(.205,.30,.105),0),
 ("","center","base",(0,1.18,0),(.165,.17,.10),0),
]
def bilateral(region,layer,x,y,z,rx,ry,rz,tilt=0):
    for sign,side in ((-1,"R"),(1,"L")):
        PARTS.append((region,side,layer,(sign*x,y,z),(rx,ry,rz),sign*tilt))

for args in [
 ("","base",.30,.88,0,.065,.19,.062,-12),
 ("","base",.37,1.17,0,.047,.15,.047,-10),
 ("","base",.40,1.35,0,.039,.075,.042,-8),
 ("","base",.105,1.53,0,.087,.27,.075,2),
 ("","base",.115,1.82,0,.051,.09,.053,0),
 ("","base",.115,2.00,0,.045,.18,.046,0),
 ("","base",.115,2.22,.045,.056,.057,.105,0),
 ("upper_pec","surface",.105,.73,.108,.112,.061,.038,-12),
 ("sternal_pec","surface",.105,.82,.116,.116,.078,.045,10),
 ("front_delt","surface",.235,.72,.076,.064,.102,.048,-20),
 ("side_delt","surface",.271,.76,0,.064,.112,.066,-14),
 ("rear_delt","surface",.229,.73,-.073,.065,.10,.049,-22),
 ("upper_trap","surface",.116,.65,-.056,.108,.054,.058,25),
 ("mid_trap","surface",.09,.78,-.113,.086,.075,.035,22),
 ("lower_trap","surface",.053,.91,-.112,.053,.112,.030,-21),
 ("rhomboids","deep",.10,.83,-.084,.064,.094,.029,-27),
 ("lats","surface",.159,.94,-.073,.091,.19,.058,-21),
 ("erectors","deep",.045,1.065,-.082,.035,.18,.029,0),
 ("biceps","surface",.307,.91,.055,.047,.125,.044,-12),
 ("brachialis","deep",.32,.96,.018,.045,.080,.046,-12),
 ("triceps_long","surface",.285,.92,-.056,.042,.128,.045,-12),
 ("triceps_other","surface",.326,.92,-.040,.040,.112,.050,-12),
 ("forearm_flexors","surface",.366,1.15,.032,.039,.133,.036,-10),
 ("forearm_extensors","surface",.366,1.15,-.032,.038,.135,.035,-10),
 ("rectus_abs","surface",.047,.965,.112,.044,.068,.029,0),
 ("rectus_abs","surface",.047,1.087,.106,.043,.069,.029,0),
 ("obliques","surface",.131,1.064,.071,.049,.15,.038,-12),
 ("glute_max","surface",.105,1.25,-.091,.100,.121,.064,0),
 ("glute_med","deep",.155,1.169,-.027,.058,.097,.057,-21),
 ("rectus_femoris","surface",.101,1.50,.071,.049,.213,.048,3),
 ("vastus_lateral","surface",.154,1.49,.031,.062,.224,.054,-6),
 ("vastus_medial","surface",.061,1.64,.049,.046,.108,.050,10),
 ("adductors","deep",.056,1.46,0,.050,.166,.053,-8),
 ("ham_lateral","surface",.146,1.51,-.055,.049,.219,.045,-4),
 ("ham_medial","surface",.066,1.51,-.056,.046,.207,.046,4),
 ("gastroc","surface",.115,1.94,-.045,.073,.147,.050,0),
 ("soleus","deep",.115,2.01,-.016,.062,.157,.046,0),
 ("tibialis","surface",.128,1.98,.033,.041,.165,.035,0),
]: bilateral(*args)

def faces(part, rings=6, segments=12):
    """Generate a tessellated ellipsoid in object coordinates."""
    key,side,layer,center,radii,tilt=part
    cx,cy,cz=center;rx,ry,rz=radii
    a=math.radians(tilt);c=math.cos(a);s=math.sin(a)
    def point(i,j):
        phi=math.pi*i/rings;theta=2*math.pi*j/segments
        x=rx*math.sin(phi)*math.cos(theta);y=ry*math.cos(phi);z=rz*math.sin(phi)*math.sin(theta)
        return (cx+c*x-s*y,cy+s*x+c*y,cz+z)
    for i in range(rings):
        for j in range(segments):
            p=[point(i,j),point(i,j+1),point(i+1,j+1),point(i+1,j)]
            # At poles two vertices coincide; retain one nondegenerate triangle.
            if i==0:p=p[1:]
            elif i==rings-1:p=p[:3]
            yield p

def rotate(p,yaw,pitch=0):
    x,y,z=p;y-=1.30
    a=math.radians(yaw);b=math.radians(pitch)
    c=math.cos(a);s=math.sin(a);x,z=x*c+z*s,-x*s+z*c
    c=math.cos(b);s=math.sin(b);y,z=y*c-z*s,y*s+z*c
    return x,y,z

def _normal(p,center):
    a,b,c=p[:3];u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
    n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
    length=math.sqrt(sum(q*q for q in n))
    if length<1e-12:return (0,0,0)
    n=[q/length for q in n];mid=[sum(q[i] for q in p)/len(p) for i in range(3)]
    if sum(n[i]*(mid[i]-center[i]) for i in range(3))<0:n=[-q for q in n]
    return n

def scene(yaw=0,pitch=0,layer="surface",isolated=None):
    """Visible polygons, far-to-near; independent of Tk."""
    if layer not in ("surface","deep","all"):raise ValueError("Invalid layer")
    result=[]
    for part in PARTS:
        key,side,depth,center,*_=part
        if isolated is not None and key not in ("",isolated):continue
        if depth!="base" and layer!="all" and depth!=layer and key!=isolated:continue
        if layer=="deep" and depth=="base":continue
        rc=rotate(center,yaw,pitch)
        for face in faces(part):
            p=[rotate(v,yaw,pitch) for v in face]
            n=_normal(p,rc)
            if n[2]<=0:continue
            light=max(0,min(1,n[2]*.78-n[0]*.36-n[1]*.18))
            result.append((sum(v[2] for v in p)/len(p),key,side,light,p))
    result.sort(key=lambda row:row[0])
    return result

"""Educational sagittal-plane joint motion; no patient data or prescription."""
import math
EXERCISES={
 "Biceps curl":("elbow", "Elbow flexion and extension", ("Biceps brachii","Brachialis")),
 "Squat":("knee", "Hip and knee flexion and extension", ("Quadriceps","Gluteals")),
 "Romanian deadlift":("hip", "Hip flexion and extension", ("Hamstrings","Gluteals")),
 "Overhead press":("elbow", "Shoulder elevation and elbow extension", ("Deltoids","Triceps")),
}
def joint_angle(a,b,c):
    u=[x-y for x,y in zip(a,b)];v=[x-y for x,y in zip(c,b)]
    if len(a)!=len(b) or len(b)!=len(c) or len(a) not in (2,3):raise ValueError("Use matching 2D or 3D points.")
    if not all(math.isfinite(x) for x in (*u,*v)):raise ValueError("Nonfinite point.")
    d=math.hypot(*u)*math.hypot(*v)
    if d<1e-12:raise ValueError("Coincident joint points.")
    return math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(u,v))/d))))
def point(start,length,angle):
    r=math.radians(angle)
    return (start[0]+length*math.cos(r),start[1]+length*math.sin(r))
def frame(exercise,phase):
    if exercise not in EXERCISES or not isinstance(phase,(int,float)) or not math.isfinite(phase) or not 0<=phase<=1:raise ValueError("Invalid animation frame.")
    # 0 and 1 = start, .5 = end of first movement. Smooth illustrative interpolation.
    t=(1-math.cos(2*math.pi*phase))/2
    ankle=(0,1.65)
    knee=point(ankle,.43,-90)
    hip=point(knee,.43,-90)
    shoulder=point(hip,.52,-90)
    elbow=point(shoulder,.30,90)
    wrist=point(elbow,.27,90)
    if exercise=="Biceps curl":
        wrist=point(elbow,.27,90-135*t)
    elif exercise=="Squat":
        knee=point(ankle,.43,-90+25*t)
        hip=point(knee,.43,-90-65*t)
        shoulder=point(hip,.52,-90+25*t)
        elbow=point(shoulder,.30,35)
        wrist=point(elbow,.27,-45)
    elif exercise=="Romanian deadlift":
        knee=point(ankle,.43,-90+8*t)
        hip=point(knee,.43,-90-14*t)
        shoulder=point(hip,.52,-90+70*t)
        elbow=point(shoulder,.30,90)
        wrist=point(elbow,.27,90)
    elif exercise=="Overhead press":
        elbow=point(shoulder,.30,10-100*t)
        wrist=point(elbow,.27,-90)
    head=point(shoulder,.22,-90)
    pts=dict(ankle=ankle,knee=knee,hip=hip,shoulder=shoulder,elbow=elbow,wrist=wrist,head=head)
    angles={"knee":joint_angle(ankle,knee,hip),"hip":joint_angle(knee,hip,shoulder),
            "shoulder":joint_angle(hip,shoulder,elbow),"elbow":joint_angle(shoulder,elbow,wrist)}
    return {"points":pts,"angles":angles,"phase":phase}

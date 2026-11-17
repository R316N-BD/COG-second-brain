"""Educational muscle relationships; explicit exact aliases, no diagnostic inference."""
import datetime as dt
import re
from .physique_training import date

MUSCLES={
    "chest":("Pectorals","Horizontal shoulder adduction and pressing."),
    "delts":("Deltoids","Shoulder elevation, flexion and extension; varies by head."),
    "lats":("Latissimus dorsi","Shoulder adduction and extension."),
    "upper_back":("Upper back","Scapular retraction and stabilization."),
    "biceps":("Elbow flexors","Elbow flexion; biceps also supinates forearm."),
    "triceps":("Triceps","Elbow extension."),
    "abs":("Abdominals","Trunk flexion and stabilization."),
    "glutes":("Gluteals","Hip extension and pelvic stabilization."),
    "quads":("Quadriceps","Knee extension."),
    "hamstrings":("Hamstrings","Knee flexion and hip extension."),
    "calves":("Calves","Ankle plantar flexion."),
}
# Primary and secondary classifications are educational approximations, not EMG or tissue stress.
EXERCISES={
    "bench press":(("chest",),("delts","triceps")),
    "incline bench press":(("chest",),("delts","triceps")),
    "incline dumbbell press":(("chest",),("delts","triceps")),
    "dumbbell bench press":(("chest",),("delts","triceps")),
    "cable fly":(("chest",),("delts",)),
    "shoulder press":(("delts",),("triceps",)),
    "lateral raise":(("delts",),()),
    "reverse pec deck":(("delts",),("upper_back",)),
    "chest supported row":(("upper_back","lats"),("biceps","delts")),
    "seated cable row":(("upper_back","lats"),("biceps","delts")),
    "lat pulldown":(("lats",),("biceps","upper_back")),
    "pull up":(("lats",),("biceps","upper_back")),
    "biceps curl":(("biceps",),()),
    "triceps extension":(("triceps",),()),
    "triceps pushdown":(("triceps",),()),
    "squat":(("quads","glutes"),("abs",)),
    "romanian deadlift":(("hamstrings","glutes"),("upper_back",)),
    "leg press":(("quads","glutes"),()),
    "leg extension":(("quads",),()),
    "leg curl":(("hamstrings",),()),
    "seated leg curl":(("hamstrings",),()),
    "calf raise":(("calves",),()),
    "crunch":(("abs",),()),
    "abdominal exercise":(("abs",),()),
}
ALIASES={"lateral raises":"lateral raise","biceps curls":"biceps curl","triceps extensions":"triceps extension",
         "calf raises":"calf raise","barbell bench press":"bench press","barbell squat":"squat",
         "rdl":"romanian deadlift","pull ups":"pull up","chest supported rows":"chest supported row"}
def normalize(name):
    return re.sub(r"[^a-z0-9]+"," ",name.casefold()).strip()

def relationship(name):
    key=normalize(name)
    return EXERCISES.get(ALIASES.get(key,key))

def muscle_history(sets,muscle,today=None,days=30):
    if muscle not in MUSCLES or type(days) is not int or not 1<=days<=365:
        raise ValueError("Unknown muscle or unsupported period.")
    today=today or dt.date.today()
    start=today-dt.timedelta(days=days-1)
    direct=secondary=unknown=0; rows=[]
    for row in sets:
        if not start<=date(row["date"])<=today:continue
        relation=relationship(row["exercise"])
        if relation is None:
            unknown+=1;continue
        kind="Primary" if muscle in relation[0] else "Secondary" if muscle in relation[1] else None
        if kind:
            direct+=kind=="Primary";secondary+=kind=="Secondary"
            rows.append((row["date"],row["exercise"],row["reps"],row["weight_kg"],kind))
    return {"primary":direct,"secondary":secondary,"unclassified":unknown,
            "rows":sorted(rows,reverse=True),
            "exercises":sorted(k for k,(a,b) in EXERCISES.items() if muscle in a or muscle in b)}

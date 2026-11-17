"""Original educational region catalog and conservative exercise associations."""
import datetime as dt
from .physique_anatomy import normalize, ALIASES
from .physique_training import date

# Broad group, common name, action summary. These are educational subdivisions,
# not measurements of isolated recruitment or individualized anatomy.
REGIONS={
 "upper_pec":("chest","Upper pectoralis major","Clavicular fibers assist shoulder flexion and horizontal adduction."),
 "sternal_pec":("chest","Sternocostal pectoralis major","Adducts and internally rotates the humerus; assists horizontal adduction."),
 "front_delt":("delts","Anterior deltoid","Shoulder flexion and horizontal adduction."),
 "side_delt":("delts","Middle deltoid","Shoulder abduction."),
 "rear_delt":("delts","Posterior deltoid","Shoulder extension and horizontal abduction."),
 "upper_trap":("upper_back","Upper trapezius","Scapular elevation and upward rotation."),
 "mid_trap":("upper_back","Middle trapezius","Scapular retraction."),
 "lower_trap":("upper_back","Lower trapezius","Scapular depression and upward rotation."),
 "rhomboids":("upper_back","Rhomboids","Scapular retraction and downward rotation; deep to trapezius."),
 "lats":("lats","Latissimus dorsi","Shoulder extension, adduction and internal rotation."),
 "erectors":("upper_back","Spinal erectors","Spinal extension and postural stabilization."),
 "biceps":("biceps","Biceps brachii","Elbow flexion and forearm supination."),
 "brachialis":("biceps","Brachialis","Elbow flexion, deep to biceps."),
 "triceps_long":("triceps","Triceps long head","Elbow extension; also assists shoulder extension."),
 "triceps_other":("triceps","Triceps lateral / medial heads","Elbow extension; medial head lies partly deep."),
 "forearm_flexors":("forearms","Forearm flexor group","Wrist and finger flexion; grip."),
 "forearm_extensors":("forearms","Forearm extensor group","Wrist and finger extension."),
 "rectus_abs":("abs","Rectus abdominis","Trunk flexion and abdominal stabilization."),
 "obliques":("abs","Oblique group","Trunk rotation, lateral flexion and stabilization."),
 "glute_max":("glutes","Gluteus maximus","Hip extension and external rotation."),
 "glute_med":("glutes","Gluteus medius","Hip abduction and pelvic stabilization."),
 "rectus_femoris":("quads","Rectus femoris","Knee extension and hip flexion."),
 "vastus_lateral":("quads","Vastus lateralis","Knee extension."),
 "vastus_medial":("quads","Vastus medialis","Knee extension."),
 "adductors":("adductors","Hip adductor group","Hip adduction; actions vary by muscle and position."),
 "ham_lateral":("hamstrings","Biceps femoris","Knee flexion; long head assists hip extension."),
 "ham_medial":("hamstrings","Medial hamstrings","Semitendinosus and semimembranosus assist knee flexion and hip extension."),
 "gastroc":("calves","Gastrocnemius","Ankle plantar flexion and knee flexion."),
 "soleus":("calves","Soleus","Ankle plantar flexion; deep to gastrocnemius."),
 "tibialis":("shins","Tibialis anterior","Ankle dorsiflexion and inversion."),
}
# Only explicitly mapped exercise-region relationships get counted. No automatic
# allocation from a broad muscle to all subdivisions.
DETAIL={
 "bench press":(("upper_pec","sternal_pec"),("front_delt","triceps_long","triceps_other")),
 "incline bench press":(("upper_pec","sternal_pec"),("front_delt","triceps_long","triceps_other")),
 "incline dumbbell press":(("upper_pec","sternal_pec"),("front_delt","triceps_long","triceps_other")),
 "dumbbell bench press":(("upper_pec","sternal_pec"),("front_delt","triceps_long","triceps_other")),
 "cable fly":(("upper_pec","sternal_pec"),("front_delt",)),
 "shoulder press":(("front_delt","side_delt"),("triceps_long","triceps_other")),
 "lateral raise":(("side_delt",),("upper_trap",)),
 "reverse pec deck":(("rear_delt",),("mid_trap","rhomboids")),
 "chest supported row":(("lats","mid_trap","rhomboids"),("rear_delt","biceps","brachialis")),
 "seated cable row":(("lats","mid_trap","rhomboids"),("rear_delt","biceps","brachialis")),
 "lat pulldown":(("lats",),("biceps","brachialis","lower_trap")),
 "pull up":(("lats",),("biceps","brachialis","lower_trap")),
 "biceps curl":(("biceps","brachialis"),("forearm_flexors",)),
 "triceps extension":(("triceps_long","triceps_other"),()),
 "triceps pushdown":(("triceps_long","triceps_other"),()),
 "squat":(("rectus_femoris","vastus_lateral","vastus_medial","glute_max"),("adductors","erectors","obliques","rectus_abs")),
 "romanian deadlift":(("ham_lateral","ham_medial","glute_max"),("erectors","forearm_flexors")),
 "leg press":(("rectus_femoris","vastus_lateral","vastus_medial","glute_max"),("adductors",)),
 "leg extension":(("rectus_femoris","vastus_lateral","vastus_medial"),()),
 "leg curl":(("ham_lateral","ham_medial"),()),
 "seated leg curl":(("ham_lateral","ham_medial"),()),
 "calf raise":(("gastroc","soleus"),()),
 "crunch":(("rectus_abs",),("obliques",)),
 "shrug":(("upper_trap",),()),
 "face pull":(("rear_delt","mid_trap"),("rhomboids",)),
 "hammer curl":(("brachialis","biceps"),()),
 "wrist curl":(("forearm_flexors",),()),
 "reverse wrist curl":(("forearm_extensors",),()),
 "hip thrust":(("glute_max",),()),
 "hip abduction":(("glute_med",),()),
 "hip adduction":(("adductors",),()),
 "seated calf raise":(("soleus",),("gastroc",)),
 "tibialis raise":(("tibialis",),()),
 "side plank":(("obliques",),("glute_med",)),
 "back extension":(("erectors",),("glute_max","ham_lateral","ham_medial")),
}
EXTRA_ALIASES={"shrugs":"shrug","face pulls":"face pull","hammer curls":"hammer curl","hip thrusts":"hip thrust","seated calf raises":"seated calf raise","tibialis raises":"tibialis raise","overhead triceps extension":"triceps extension"}
def detailed_relationship(name):
    k=normalize(name)
    return DETAIL.get(EXTRA_ALIASES.get(k,ALIASES.get(k,k)))

def region_history(sets,region,days=30,today=None):
    if region not in REGIONS or type(days) is not int or not 1<=days<=365:
        raise ValueError("Unknown region or unsupported period.")
    today=today or dt.date.today()
    start=today-dt.timedelta(days=days-1)
    rows=[];primary=secondary=unknown=0; sessions=set()
    for r in sets:
        if not start<=date(r["date"])<=today:continue
        mapping=detailed_relationship(r["exercise"])
        if mapping is None:
            unknown+=1;continue
        kind="Primary" if region in mapping[0] else "Secondary" if region in mapping[1] else None
        if kind:
            primary+=kind=="Primary";secondary+=kind=="Secondary"
            sessions.add(r["date"])
            rows.append((r["date"],r["exercise"],r["reps"],r["weight_kg"],kind))
    return {"primary":primary,"secondary":secondary,"unclassified":unknown,
            "sessions":len(sessions),"last_date":max(sessions) if sessions else None,
            "rows":sorted(rows,reverse=True),
            "primary_exercises":sorted(k for k,(a,b) in DETAIL.items() if region in a),
            "secondary_exercises":sorted(k for k,(a,b) in DETAIL.items() if region in b)}

def body_counts(sets,days=30,today=None):
    return {k:region_history(sets,k,days,today) for k in REGIONS}


def period_comparison(sets,region,days=30,today=None):
    today=today or dt.date.today()
    current=region_history(sets,region,days,today)
    prior=region_history(sets,region,days,today-dt.timedelta(days=days))
    return {"current":current,"prior":prior,
            "primary_change":current["primary"]-prior["primary"],
            "secondary_change":current["secondary"]-prior["secondary"]}

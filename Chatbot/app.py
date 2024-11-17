from flask import Flask, render_template, request, jsonify
from sympy import solve as sympy_solve, symbols, Eq, sympify, expand, collect, Poly
import re
import math

app = Flask(__name__)

def extrahiere_gleichung(eingabe):
    # Grundlegende Bereinigung
    eingabe = eingabe.strip().strip("'").strip('"')
    eingabe = eingabe.lower().replace("berechne", "").replace("löse", "").strip()
    eingabe = eingabe.replace(" ", "")
    
    # Ersetze ² durch ^2
    eingabe = eingabe.replace("²", "^2")
    
    # Verarbeite Brüche
    def verarbeite_bruch(match):
        zaehler, nenner = map(float, match.group().split('/'))
        return str(zaehler / nenner)
    
    eingabe = re.sub(r'\d+/\d+', verarbeite_bruch, eingabe)
    
    # Füge implizite Multiplikationen hinzu
    eingabe = re.sub(r'(\d)x', r'\1*x', eingabe)
    eingabe = re.sub(r'(^|[+\-=])x\^2', r'\g<1>1*x^2', eingabe)
    eingabe = re.sub(r'(^|[+\-=])x([+\-=]|$)', r'\g<1>1*x\2', eingabe)
    
    # Ersetze ^ durch **
    eingabe = eingabe.replace("^2", "**2")
    
    # Normalisiere mathematische Ausdrücke
    eingabe = eingabe.replace(" gleich ", "=").replace("ist gleich", "=")
    eingabe = eingabe.replace(" plus ", "+").replace(" minus ", "-")
    eingabe = eingabe.replace(" mal ", "*").replace(" geteilt durch ", "/")
    
    # Bereinige Leerzeichen um Operatoren
    eingabe = re.sub(r'\s*([+\-*/=])\s*', r'\1', eingabe)
    
    # Füge =0 hinzu, wenn kein Gleichheitszeichen vorhanden
    if "=" not in eingabe:
        eingabe += "=0"
    
    return eingabe

def formatiere_gleichung(gleichung_str):
    gleichung = gleichung_str.replace("**2", "²")
    gleichung = gleichung.replace("*", "·")
    gleichung = re.sub(r'([+-])', r' \1 ', gleichung)
    gleichung = re.sub(r'\s+', ' ', gleichung)
    return gleichung.strip()

def berechne_mitternachtsformel(a, b, c):
    diskriminante = b**2 - 4*a*c
    
    schritte = []
    schritte.append("\n📝 Die Mitternachtsformel lautet:")
    schritte.append("   x = -b ± √(b² - 4ac) / (2a)")
    schritte.append(f"\n💡 Einsetzen der Werte:")
    schritte.append(f"   a = {a}")
    schritte.append(f"   b = {b}")
    schritte.append(f"   c = {c}")
    schritte.append(f"\n🔢 Berechnung:")
    schritte.append(f"   x = -({b}) ± √({b}² - 4·{a}·{c}) / (2·{a})")
    schritte.append(f"   x = {-b} ± √({b**2} - {4*a*c}) / {2*a}")
    schritte.append(f"   x = {-b} ± √({diskriminante}) / {2*a}")
    
    if diskriminante > 0:
        x1 = (-b + math.sqrt(diskriminante)) / (2*a)
        x2 = (-b - math.sqrt(diskriminante)) / (2*a)
        schritte.append(f"\n✨ Ergebnisse:")
        schritte.append(f"   x₁ = ({-b} + √{diskriminante}) / {2*a} = {x1:.3f}")
        schritte.append(f"   x₂ = ({-b} - √{diskriminante}) / {2*a} = {x2:.3f}")
        return schritte, [x1, x2], "zwei reelle Lösungen"
    elif diskriminante == 0:
        x = -b / (2*a)
        schritte.append(f"\n✨ Ergebnis:")
        schritte.append(f"   x = {-b} / {2*a} = {x:.3f}")
        return schritte, [x], "eine doppelte Lösung"
    else:
        schritte.append("\n❌ Die Diskriminante ist negativ, daher gibt es keine reellen Lösungen.")
        return schritte, None, "keine reellen Lösungen"

def formatiere_rechenweg(gleichung, schritte, loesung):
    rechenweg = ["📐 Hier ist der Rechenweg:\n"]
    
    formatierte_gleichung = formatiere_gleichung(gleichung)
    rechenweg.append(f"1️⃣ Ausgangsgleichung:")
    rechenweg.append(f"   {formatierte_gleichung}")
    
    for schritt in schritte:
        if schritt.startswith("Dies ist"):
            rechenweg.append(f"\n🔍 {schritt}")
        else:
            rechenweg.append(f"{schritt}")
    
    if isinstance(loesung, list):
        if len(loesung) == 2:
            rechenweg.append(f"\n🎯 Lösungen:")
            rechenweg.append(f"   x₁ = {loesung[0]:.3f}")
            rechenweg.append(f"   x₂ = {loesung[1]:.3f}")
        else:
            rechenweg.append(f"\n🎯 Lösung:")
            rechenweg.append(f"   x = {loesung[0]:.3f}")
    elif loesung == "keine reellen Lösungen":
        rechenweg.append(f"\n❌ Diese Gleichung hat keine reellen Lösungen")
    else:
        rechenweg.append(f"\n🎯 Lösung:")
        rechenweg.append(f"   x = {loesung}")
    
    return "\n".join(rechenweg)

def loese_gleichung(eingabe):
    try:
        # Extrahiere und normalisiere die Gleichung
        gleichung_str = extrahiere_gleichung(eingabe)
        links, rechts = gleichung_str.split("=")
        
        # Symbolvariable für x
        x = symbols('x')
        
        try:
            # Konvertiere die Gleichung in einen SymPy-Ausdruck
            gleichung = sympify(links) - sympify(rechts)
            
            # Expandiere den Ausdruck
            vereinfacht = expand(gleichung)
            
            # Erstelle ein Polynom-Objekt
            poly = Poly(vereinfacht, x)
            
            # Hole die Koeffizienten
            koeffizienten = poly.all_coeffs()
            
            # Bestimme den Grad des Polynoms
            grad = len(koeffizienten) - 1
            
            schritte = []
            
            if grad == 2:
                # Quadratische Gleichung: ax² + bx + c = 0
                a = float(koeffizienten[0])
                b = float(koeffizienten[1]) if len(koeffizienten) > 1 else 0
                c = float(koeffizienten[2]) if len(koeffizienten) > 2 else 0
                
                schritte.append(f"\n🔍 Dies ist eine quadratische Gleichung in der Form: {a}x² + {b}x + {c} = 0")
                schritte.append("Wir verwenden die Mitternachtsformel zur Lösung:")
                
                mitternacht_schritte, loesungen, typ = berechne_mitternachtsformel(a, b, c)
                schritte.extend(mitternacht_schritte)
                
                if loesungen:
                    return formatiere_rechenweg(gleichung_str, schritte, loesungen)
                else:
                    return formatiere_rechenweg(gleichung_str, schritte, "keine reellen Lösungen")
            else:
                # Lineare Gleichung
                loesung = sympy_solve(gleichung)
                schritte.append("\n🔍 Dies ist eine lineare Gleichung")
                schritte.append("Isoliere x durch Umformen")
                return formatiere_rechenweg(gleichung_str, schritte, loesung[0])
            
        except Exception as e:
            raise e
            
    except Exception as e:
        return f"Entschuldigung, ich konnte diese Gleichung nicht lösen. Bitte gib die Gleichung in einer klaren Form ein, zum Beispiel:\n- '2*x + 3 = 7'\n- '3*x - 5 = 10'\n- '3x^2 + 2x - 1 = 0'\n\nFehler: {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    try:
        data = request.get_json()
        equation = data.get('equation', '').strip()
        response = loese_gleichung(equation)
        return jsonify({'solution': response})
    except Exception as e:
        return jsonify({'error': f"Ein Fehler ist aufgetreten: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)

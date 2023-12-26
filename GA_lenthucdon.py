from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:201arsenal@localhost:3306/meals'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True  # This line enables auto-reloading of templates
app.config['JSON_AS_ASCII'] = False  # This line prevents ASCII encoding for JSON responses
db = SQLAlchemy(app)

class mon_an(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ten_mon_an = db.Column(db.String(50), nullable=False)
    gia_tri_dinh_duong = db.Column(db.Float, nullable=False)
    gia_tien = db.Column(db.Float, nullable=False)
    phan_loai = db.Column(db.String, nullable=False)
    mo_ta = db.Column(db.String(255), nullable=True)

calo_max = 500
# class Individual:
#     def __init__(self):
#         self.selected_mon_an = []

#     def add_mon_an(self, mon_an):
#         self.selected_mon_an.append(mon_an)

#     def get_total_nutrition_value(self):
#         return sum(mon_an.gia_tri_dinh_duong for mon_an in self.selected_mon_an)

#     def get_total_cost(self):
#         return sum(mon_an.gia_tien for mon_an in self.selected_mon_an)

# Hàm tạo quần thể ban đầu
def create_population_from_database(population_size):
    # Fetch all rows from the 'mon_an' table
    rows = mon_an.query.all()

    population = []
    for _ in range(population_size):
        genes = random.sample(rows, k=random.randint(3, 5))
        population.append({"genes": genes})

    return population

def fitness(individual, price_max, calories_min):
    total_calories = sum(food.gia_tri_dinh_duong for food in individual["genes"])
    total_price = sum(food.gia_tien for food in individual["genes"])
    nutrients = {food.phan_loai for food in individual["genes"]}
    required_nutrients = {"protein", "carb", "fiber"}
    
    if total_calories < calo_max and total_calories > calories_min and total_price < price_max and required_nutrients.issubset(nutrients):
        return total_calories
    else:
        return 0

def crossover(parent1, parent2):
    genes1 = parent1["genes"].copy()
    genes2 = parent2["genes"].copy()

    crossover_point = random.randint(1, min(len(genes1), len(genes2)) - 1)

    child_genes = genes1[:crossover_point]

    for gene in genes2:
        if gene not in child_genes:
            child_genes.append(gene)

    return {"genes": child_genes}

def mutate(individual):
    # individual = Individual()
    mutated_gene = random.choice(mon_an.query.all())
    mutation_point = random.randint(0, len(individual["genes"]) - 1)
    while mutated_gene in individual["genes"]:
        mutated_gene = random.choice(mon_an.query.all())
    individual["genes"][mutation_point] = mutated_gene
    return individual

def selection(population, calories_min, price_max):
    selected = sorted(population, key=lambda x: fitness(x, price_max, calories_min), reverse=True)
    if fitness(selected[0], price_max, calories_min) == 0:
        selected[0] = max(population, key=lambda x: fitness(x, price_max, calories_min))
    return selected

def genetic_algorithm_from_database(population_size, generations, calories_min, price_max):
    population = create_population_from_database(population_size)

    for generation in range(generations):
        population = sorted(population, key=lambda x: fitness(x, price_max, calories_min), reverse=True)
        new_population = []

        for _ in range(population_size // 2):
            parent1 = selection(population, calories_min, price_max)[0]
            parent2 = selection(population, calories_min, price_max)[0]

            child1 = crossover(parent1, parent2)
            child1 = mutate(child1)

            child2 = crossover(parent2, parent1)
            child2 = mutate(child2)

            new_population.extend([child1, child2])

        population = new_population

    best_individual = max(population, key=lambda x: fitness(x, price_max, calories_min))

    return best_individual

def result_from_mysql(calories_min, price_max):
    meals = []
    for x in range(7):
        bua_an = genetic_algorithm_from_database(population_size=200, generations=50, calories_min=calories_min, price_max=price_max)
        meal_info = [
            {
                'ten_mon_an': food.ten_mon_an,
                'gia_tri_dinh_duong': food.gia_tri_dinh_duong,
                'gia_tien': food.gia_tien,
                'phan_loai': food.phan_loai,
                'mo_ta': food.mo_ta
            }
            for food in bua_an["genes"]
        ]
        meals.append({'bua_an': x + 1, 'foods': meal_info})

    return meals

@app.route('/')
def index():
    # all_meals = mon_an.query.all()
    return render_template('index.html',mess="")

@app.route('/generate_plan', methods=['POST'])
def generate_plan():
    max_budget = float(request.form['max_budget']) * 20
    min_nutrition_value = float(request.form['min_nutrition_value'])
    if(min_nutrition_value < 300 or min_nutrition_value > 500):
        return render_template('index.html', mess="lỗi số liệu!!! Số calo 1 đứa trẻ trong khoảng 360-500 calo")
    elif(max_budget < 200000 or max_budget > 600000):
        return render_template('index.html', mess="lỗi số liệu!!! Số tiền trong khoảng 15000-30000vnd")
    else :
        meals = result_from_mysql(calories_min=min_nutrition_value, price_max=max_budget)
        return render_template('result.html', meals=meals)
if __name__ == '__main__':
    app.run(debug=True)
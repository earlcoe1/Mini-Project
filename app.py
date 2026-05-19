from flask import Flask, request, jsonify, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy
import plotly.express as px
import pandas as pd
import os

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///agriculture.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Crop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(100), nullable=False)
    season = db.Column(db.String(50), nullable=False)
    rainfall = db.Column(db.Float, nullable=False)
    soil_condition = db.Column(db.String(100), nullable=False)
    fertilizer_used = db.Column(db.Float, nullable=False)
    yield_amount = db.Column(db.Float, nullable=False)

    def performance_status(self):
        if self.yield_amount >= 80:
            return "High Yield"
        elif self.yield_amount >= 50:
            return "Moderate Yield"
        return "Low Yield"

    def to_dict(self):
        return {
            "id": self.id,
            "crop_name": self.crop_name,
            "season": self.season,
            "rainfall": self.rainfall,
            "soil_condition": self.soil_condition,
            "fertilizer_used": self.fertilizer_used,
            "yield_amount": self.yield_amount,
            "performance": self.performance_status()
        }


with app.app_context():
    db.create_all()


HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Agriculture Analytics API</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f7f4;
            margin: 0;
            padding: 0;
        }
        header {
            background: #1f7a3f;
            color: white;
            padding: 25px;
            text-align: center;
        }
        .container {
            width: 92%;
            margin: 25px auto;
        }
        .card {
            background: white;
            padding: 22px;
            margin-bottom: 25px;
            border-radius: 10px;
            box-shadow: 0 3px 8px rgba(0,0,0,0.12);
        }
        input, select {
            padding: 10px;
            width: 100%;
            margin: 8px 0 15px;
            border: 1px solid #ccc;
            border-radius: 6px;
        }
        button {
            background: #1f7a3f;
            color: white;
            border: none;
            padding: 11px 18px;
            border-radius: 6px;
            cursor: pointer;
        }
        button:hover {
            background: #155c2e;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        th {
            background: #1f7a3f;
            color: white;
        }
        th, td {
            padding: 11px;
            border: 1px solid #ddd;
            text-align: left;
        }
        .delete-btn {
            background: #c0392b;
        }
        .summary {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .summary-box {
            background: #eaf5ec;
            padding: 18px;
            border-radius: 8px;
            flex: 1;
            min-width: 180px;
            text-align: center;
        }
        .chart-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 25px;
        }
        .note {
            background: #fff8e1;
            border-left: 5px solid #f4b400;
            padding: 14px;
            border-radius: 6px;
        }
        .low {
            color: #c0392b;
            font-weight: bold;
        }
        .moderate {
            color: #b9770e;
            font-weight: bold;
        }
        .high {
            color: #1f7a3f;
            font-weight: bold;
        }
    </style>
</head>
<body>

<header>
    <h1>Agriculture Analytics Dashboard</h1>
    <p>Crop Yield Performance Monitoring System</p>
</header>

<div class="container">

    <div class="card">
        <h2>Add Crop Record</h2>
        <form action="/add_crop_form" method="POST">
            <label>Crop Name</label>
            <input type="text" name="crop_name" required>

            <label>Season</label>
            <select name="season" required>
                <option value="">Select Season</option>
                <option value="Rainy">Rainy</option>
                <option value="Dry">Dry</option>
                <option value="Spring">Spring</option>
                <option value="Summer">Summer</option>
            </select>

            <label>Rainfall</label>
            <input type="number" step="0.01" name="rainfall" required>

            <label>Soil Condition</label>
            <select name="soil_condition" required>
                <option value="">Select Soil Condition</option>
                <option value="Good">Good</option>
                <option value="Fair">Fair</option>
                <option value="Poor">Poor</option>
            </select>

            <label>Fertilizer Used</label>
            <input type="number" step="0.01" name="fertilizer_used" required>

            <label>Yield Amount</label>
            <input type="number" step="0.01" name="yield_amount" required>

            <button type="submit">Add Crop</button>
        </form>
    </div>

    <div class="card">
        <h2>Upload CSV or Excel File</h2>
        <form action="/upload_file_web" method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept=".csv,.xlsx" required>
            <button type="submit">Upload File</button>
        </form>
    </div>

    <div class="card">
        <h2>Analytics Summary</h2>
        <div class="summary">
            <div class="summary-box">
                <h3>Total Records</h3>
                <p>{{ total_records }}</p>
            </div>
            <div class="summary-box">
                <h3>Average Yield</h3>
                <p>{{ average_yield }}</p>
            </div>
            <div class="summary-box">
                <h3>High Yield</h3>
                <p>{{ high_count }}</p>
            </div>
            <div class="summary-box">
                <h3>Moderate Yield</h3>
                <p>{{ moderate_count }}</p>
            </div>
            <div class="summary-box">
                <h3>Low Yield</h3>
                <p>{{ low_count }}</p>
            </div>
        </div>
        <p><strong>Business Insight:</strong> Crops below 50 yield need attention because poor rainfall, soil condition, or fertilizer use may reduce productivity.</p>
    </div>

    <div class="card">
        <h2>Visualization Charts</h2>

        {% if has_data %}
            <div class="chart-grid">
                <div>
                    <h3>Crop Yield Performance Bar Chart</h3>
                    {{ yield_chart|safe }}
                </div>

                <div>
                    <h3>Yield Classification Distribution</h3>
                    {{ performance_chart|safe }}
                </div>

                <div>
                    <h3>Rainfall Compared to Crop Yield</h3>
                    {{ rainfall_yield_chart|safe }}
                </div>
            </div>
        {% else %}
            <p>No data available yet. Add a crop record or upload a CSV/Excel file to generate charts.</p>
        {% endif %}
    </div>

    <div class="card">
        <h2>Crop Records</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Crop</th>
                <th>Season</th>
                <th>Rainfall</th>
                <th>Soil</th>
                <th>Fertilizer</th>
                <th>Yield</th>
                <th>Performance</th>
                <th>Action</th>
            </tr>

            {% for crop in crops %}
            <tr>
                <td>{{ crop.id }}</td>
                <td>{{ crop.crop_name }}</td>
                <td>{{ crop.season }}</td>
                <td>{{ crop.rainfall }}</td>
                <td>{{ crop.soil_condition }}</td>
                <td>{{ crop.fertilizer_used }}</td>
                <td>{{ crop.yield_amount }}</td>
                <td class="{% if crop.performance_status() == 'High Yield' %}high{% elif crop.performance_status() == 'Moderate Yield' %}moderate{% else %}low{% endif %}">
                    {{ crop.performance_status() }}
                </td>
                <td>
                    <form action="/delete_crop_form/{{ crop.id }}" method="POST">
                        <button class="delete-btn" type="submit">Delete</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="card">
        <h2>API Endpoints</h2>
        <p>GET /crops</p>
        <p>POST /crops</p>
        <p>PUT /crops/&lt;id&gt;</p>
        <p>DELETE /crops/&lt;id&gt;</p>
        <p>POST /upload_file</p>
        <p>GET /analytics</p>
    </div>

</div>

</body>
</html>
"""


@app.route("/")
def dashboard():
    crops = Crop.query.all()
    total_records = len(crops)

    if total_records > 0:
        average_yield = round(sum(c.yield_amount for c in crops) / total_records, 2)
    else:
        average_yield = 0

    high_count = len([c for c in crops if c.yield_amount >= 80])
    moderate_count = len([c for c in crops if 50 <= c.yield_amount < 80])
    low_count = len([c for c in crops if c.yield_amount < 50])

    yield_chart = ""
    performance_chart = ""
    rainfall_yield_chart = ""
    has_data = total_records > 0

    if has_data:
        df_chart = pd.DataFrame([crop.to_dict() for crop in crops])

        fig_yield = px.bar(
            df_chart,
            x="crop_name",
            y="yield_amount",
            color="performance",
            title="Crop Yield Amount by Crop",
            labels={
                "crop_name": "Crop Name",
                "yield_amount": "Yield Amount",
                "performance": "Performance"
            }
        )
        yield_chart = fig_yield.to_html(full_html=False)

        fig_performance = px.pie(
            df_chart,
            names="performance",
            title="High, Moderate, and Low Yield Distribution"
        )
        performance_chart = fig_performance.to_html(full_html=False)

        fig_rainfall = px.scatter(
            df_chart,
            x="rainfall",
            y="yield_amount",
            color="performance",
            hover_name="crop_name",
            title="Rainfall Compared to Crop Yield",
            labels={
                "rainfall": "Rainfall",
                "yield_amount": "Yield Amount",
                "performance": "Performance"
            }
        )
        rainfall_yield_chart = fig_rainfall.to_html(full_html=False)

    return render_template_string(
        HTML_PAGE,
        crops=crops,
        total_records=total_records,
        average_yield=average_yield,
        high_count=high_count,
        moderate_count=moderate_count,
        low_count=low_count,
        has_data=has_data,
        yield_chart=yield_chart,
        performance_chart=performance_chart,
        rainfall_yield_chart=rainfall_yield_chart
    )


@app.route("/add_crop_form", methods=["POST"])
def add_crop_form():
    crop = Crop(
        crop_name=request.form["crop_name"],
        season=request.form["season"],
        rainfall=float(request.form["rainfall"]),
        soil_condition=request.form["soil_condition"],
        fertilizer_used=float(request.form["fertilizer_used"]),
        yield_amount=float(request.form["yield_amount"])
    )

    db.session.add(crop)
    db.session.commit()

    return redirect(url_for("dashboard"))


@app.route("/delete_crop_form/<int:id>", methods=["POST"])
def delete_crop_form(id):
    crop = Crop.query.get_or_404(id)
    db.session.delete(crop)
    db.session.commit()

    return redirect(url_for("dashboard"))


@app.route("/upload_file_web", methods=["POST"])
def upload_file_web():
    file = request.files.get("file")

    if not file:
        return redirect(url_for("dashboard"))

    if file.filename.endswith(".csv"):
        df = pd.read_csv(file)
    elif file.filename.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        return redirect(url_for("dashboard"))

    required_columns = [
        "crop_name",
        "season",
        "rainfall",
        "soil_condition",
        "fertilizer_used",
        "yield_amount"
    ]

    for col in required_columns:
        if col not in df.columns:
            return redirect(url_for("dashboard"))

    for _, row in df.iterrows():
        crop = Crop(
            crop_name=row["crop_name"],
            season=row["season"],
            rainfall=float(row["rainfall"]),
            soil_condition=row["soil_condition"],
            fertilizer_used=float(row["fertilizer_used"]),
            yield_amount=float(row["yield_amount"])
        )
        db.session.add(crop)

    db.session.commit()

    return redirect(url_for("dashboard"))


@app.route("/crops", methods=["GET"])
def get_crops():
    crops = Crop.query.all()
    return jsonify([crop.to_dict() for crop in crops]), 200


@app.route("/crops", methods=["POST"])
def add_crop():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON data is required"}), 400

    required_fields = [
        "crop_name",
        "season",
        "rainfall",
        "soil_condition",
        "fertilizer_used",
        "yield_amount"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    crop = Crop(
        crop_name=data["crop_name"],
        season=data["season"],
        rainfall=float(data["rainfall"]),
        soil_condition=data["soil_condition"],
        fertilizer_used=float(data["fertilizer_used"]),
        yield_amount=float(data["yield_amount"])
    )

    db.session.add(crop)
    db.session.commit()

    return jsonify({
        "message": "Crop record added successfully",
        "crop": crop.to_dict()
    }), 201


@app.route("/crops/<int:id>", methods=["PUT"])
def update_crop(id):
    crop = Crop.query.get(id)

    if not crop:
        return jsonify({"error": "Crop record not found"}), 404

    data = request.get_json()

    crop.crop_name = data.get("crop_name", crop.crop_name)
    crop.season = data.get("season", crop.season)
    crop.rainfall = float(data.get("rainfall", crop.rainfall))
    crop.soil_condition = data.get("soil_condition", crop.soil_condition)
    crop.fertilizer_used = float(data.get("fertilizer_used", crop.fertilizer_used))
    crop.yield_amount = float(data.get("yield_amount", crop.yield_amount))

    db.session.commit()

    return jsonify({
        "message": "Crop record updated successfully",
        "crop": crop.to_dict()
    }), 200


@app.route("/crops/<int:id>", methods=["DELETE"])
def delete_crop(id):
    crop = Crop.query.get(id)

    if not crop:
        return jsonify({"error": "Crop record not found"}), 404

    db.session.delete(crop)
    db.session.commit()

    return jsonify({"message": "Crop record deleted successfully"}), 200


@app.route("/upload_file", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Use form-data with key name 'file'."}), 400

    file = request.files["file"]

    if file.filename.endswith(".csv"):
        df = pd.read_csv(file)
    elif file.filename.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        return jsonify({"error": "Only CSV or Excel files are allowed"}), 400

    required_columns = [
        "crop_name",
        "season",
        "rainfall",
        "soil_condition",
        "fertilizer_used",
        "yield_amount"
    ]

    for col in required_columns:
        if col not in df.columns:
            return jsonify({"error": f"Missing column: {col}"}), 400

    count = 0

    for _, row in df.iterrows():
        crop = Crop(
            crop_name=row["crop_name"],
            season=row["season"],
            rainfall=float(row["rainfall"]),
            soil_condition=row["soil_condition"],
            fertilizer_used=float(row["fertilizer_used"]),
            yield_amount=float(row["yield_amount"])
        )
        db.session.add(crop)
        count += 1

    db.session.commit()

    return jsonify({
        "message": "File uploaded successfully",
        "records_inserted": count
    }), 201


@app.route("/analytics", methods=["GET"])
def analytics():
    crops = Crop.query.all()

    if not crops:
        return jsonify({"message": "No crop data available"}), 200

    total_records = len(crops)
    average_yield = sum(c.yield_amount for c in crops) / total_records

    low_yield_crops = [c.to_dict() for c in crops if c.yield_amount < 50]
    moderate_yield_crops = [c.to_dict() for c in crops if 50 <= c.yield_amount < 80]
    high_yield_crops = [c.to_dict() for c in crops if c.yield_amount >= 80]

    return jsonify({
        "total_records": total_records,
        "average_yield": round(average_yield, 2),
        "low_yield_count": len(low_yield_crops),
        "moderate_yield_count": len(moderate_yield_crops),
        "high_yield_count": len(high_yield_crops),
        "low_yield_crops": low_yield_crops,
        "moderate_yield_crops": moderate_yield_crops,
        "high_yield_crops": high_yield_crops,
        "business_insight": "Crops with yield below 50 need attention. The issue may come from poor rainfall, weak soil condition, or low fertilizer usage."
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
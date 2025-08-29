#!/usr/bin/env python3
"""
FloorIQ Dashboard (IQ model preview)
- New normalization: Machine IQ (0-200, 100 avg) based on minutes/hour open
- Does not alter existing dashboard; runs on a separate port for review
"""

import math
import random
from statistics import mean, pstdev
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from flask import Flask, render_template, jsonify


HOURS_OPEN_PER_WEEK = 168  # MVP default


class FloorIQIQApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'flooriq-iq-model-2025'
        self.app.config['TEMPLATES_AUTO_RELOAD'] = True
        self.app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

        # Generate baseline equipment data (same schema as existing app, but independent)
        self.equipment_data = self.generate_equipment_data()
        # Compute IQ fields
        self.compute_iq_fields(self.equipment_data)

        self.setup_routes()

    def generate_equipment_data(self) -> List[Dict]:
        equipment_types = [
            ('Treadmill', 'Cardio'),
            ('Elliptical', 'Cardio'),
            ('Stationary Bike', 'Cardio'),
            ('Rowing Machine', 'Cardio'),
            ('Stair Climber', 'Cardio'),
            ('Squat Rack', 'Strength'),
            ('Bench Press', 'Strength'),
            ('Leg Press', 'Strength'),
            ('Lat Pulldown', 'Strength'),
            ('Cable Machine', 'Strength'),
            ('Smith Machine', 'Strength'),
            ('Leg Extension', 'Strength'),
            ('Leg Curl', 'Strength'),
            ('Chest Press', 'Strength'),
            ('Shoulder Press', 'Strength'),
            ('Pull-up Station', 'Strength'),
            ('Dip Station', 'Strength'),
            ('Cable Crossover', 'Strength'),
            ('Preacher Curl', 'Strength'),
            ('Calf Raise', 'Strength'),
            ('Hip Thrust', 'Strength'),
            ('Hack Squat', 'Strength'),
        ]

        items = []
        for i in range(55):
            equipment_type, category = random.choice(equipment_types)
            equipment_num = i + 1

            # New gym baselines (consistent with current working dashboard)
            if category == 'Cardio':
                base_minutes = random.randint(220, 520)
            else:
                base_minutes = random.randint(140, 420)

            if equipment_type in ['Squat Rack', 'Bench Press']:
                base_minutes += random.randint(60, 140)
            if equipment_type in ['Leg Extension', 'Cable Machine']:
                base_minutes = max(base_minutes - random.randint(20, 60), 90)

            roll = random.random()
            if roll < 0.7:
                growth_pct = random.uniform(0.05, 0.22)
            elif roll < 0.9:
                growth_pct = 0.0
            else:
                growth_pct = -random.uniform(0.02, 0.10)

            prev_week_minutes = int(round(base_minutes / (1 + (growth_pct if growth_pct != -1 else 0.0))))
            weekly_change = base_minutes - prev_week_minutes

            items.append({
                'id': f'equipment_{equipment_num:03d}',
                'name': f'{equipment_type} {equipment_num}',
                'type': equipment_type,
                'category': category,
                'total_minutes': base_minutes,
                'weekly_change': weekly_change,
                'trend': ('stable' if abs(weekly_change) < 25 else ('up' if weekly_change > 0 else 'down')),
                'trend_text': '—',  # will be replaced in template with pts
                'peak_hours': random.choices(
                    population=['5-8pm', '6-9am', '12-2pm', '7-9pm', '6-8pm', '--'],
                    weights=[36, 22, 12, 18, 20, 4],
                    k=1
                )[0],
                'report_period': 'Week ending Aug 18, 2025',
            })

        return items

    def compute_iq_fields(self, items: List[Dict]):
        # Compute minutes per hour (mph) for current and previous week
        for it in items:
            it['mph'] = it['total_minutes'] / HOURS_OPEN_PER_WEEK
            prev_minutes = max(0, it['total_minutes'] - it['weekly_change'])
            it['mph_prev'] = prev_minutes / HOURS_OPEN_PER_WEEK

        # Group by category for baselines
        by_cat: Dict[str, List[float]] = {}
        for it in items:
            by_cat.setdefault(it['category'], []).append(it['mph'])

        # Gym-wide baseline
        gym_mph_list = [it['mph'] for it in items]
        gym_mu = mean(gym_mph_list)
        gym_sigma = pstdev(gym_mph_list) if len(gym_mph_list) > 1 else 1.0
        if gym_sigma == 0: gym_sigma = 1.0

        # Category baselines with fallback
        cat_baselines: Dict[str, Tuple[float, float]] = {}
        for c, vals in by_cat.items():
            if len(vals) >= 5:
                mu = mean(vals)
                sigma = pstdev(vals) if len(vals) > 1 else 1.0
                if sigma == 0: sigma = 1.0
                cat_baselines[c] = (mu, sigma)
            else:
                cat_baselines[c] = (gym_mu, gym_sigma)

        def to_iq(mph: float, mu: float, sigma: float) -> int:
            z = (mph - mu) / sigma
            iq = round(100 + 15 * z)
            return max(0, min(200, iq))

        # Assign IQ and deltaIQ
        for it in items:
            mu, sigma = cat_baselines.get(it['category'], (gym_mu, gym_sigma))
            it['iq'] = to_iq(it['mph'], mu, sigma)
            it['iq_prev'] = to_iq(it['mph_prev'], mu, sigma)
            it['delta_iq'] = it['iq'] - it['iq_prev']

        # Gym IQ: mean of machine IQs
        self.gym_iq = round(mean([it['iq'] for it in items])) if items else 100
        self.gym_band = self.band_for_score(self.gym_iq)

    @staticmethod
    def band_for_score(iq: int) -> str:
        if iq < 90:
            return 'Below Average'
        elif iq <= 110:
            return 'Average'
        return 'Above Average'

    def get_current_week_label(self):
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        start_fmt_month = week_start.strftime('%b')
        end_fmt_month = week_end.strftime('%b')
        if week_start.month == week_end.month:
            label = f"{start_fmt_month} {week_start.day}–{week_end.day}, {week_end.year}"
        else:
            label = f"{start_fmt_month} {week_start.day} – {end_fmt_month} {week_end.day}, {week_end.year}"
        return label

    def setup_routes(self):
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard_iq.html',
                                   week_label=self.get_current_week_label(),
                                   gym_iq=self.gym_iq,
                                   gym_band=self.gym_band)

        @self.app.route('/api/equipment')
        def api_equipment():
            return jsonify({'success': True, 'equipment': self.equipment_data, 'total_count': len(self.equipment_data)})

        @self.app.route('/api/summary')
        def api_summary():
            return jsonify({'success': True,
                            'stats': {
                                'gym_iq': self.gym_iq,
                                'gym_band': self.gym_band,
                                'week_label': self.get_current_week_label(),
                            }})

    def run(self, host='0.0.0.0', port=8086, debug=True):
        print(f"Starting FloorIQ IQ Dashboard on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)


def main():
    app = FloorIQIQApp()
    app.run(port=8086, debug=True)


if __name__ == '__main__':
    main()


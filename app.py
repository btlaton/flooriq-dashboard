#!/usr/bin/env python3
"""
FloorIQ Dashboard - Clean Implementation
Combines the beautiful Netlify dashboard with the working equipment list
"""

import random
from flask import Flask, render_template, jsonify
from datetime import datetime

class FloorIQApp:
    """Clean Flask app combining summary dashboard and equipment list"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'flooriq-clean-2024'
        
        # Generate 55 equipment items (shared across all views)
        self.equipment_data = self.generate_equipment_data()
        
        self.setup_routes()
        print(f"FloorIQ App initialized with {len(self.equipment_data)} equipment items")
    
    def generate_equipment_data(self):
        """Generate realistic data for 55 pieces of equipment"""
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
        
        equipment_list = []
        
        for i in range(55):
            equipment_type, category = random.choice(equipment_types)
            equipment_num = i + 1
            
            # Generate realistic weekly utilization minutes
            base_minutes = random.randint(180, 650)
            
            # Equipment type adjustments
            if category == 'Cardio':
                base_minutes = random.randint(350, 750)
            elif equipment_type in ['Squat Rack', 'Bench Press', 'Leg Press']:
                base_minutes = random.randint(450, 850)
            elif equipment_type in ['Leg Extension', 'Cable Machine']:
                base_minutes = random.randint(120, 350)  # Lower for replacement candidates
            
            # Generate trend data
            prev_week_minutes = base_minutes + random.randint(-180, 180)
            weekly_change = base_minutes - prev_week_minutes
            
            if abs(weekly_change) < 25:
                trend = 'stable'
                trend_text = '—'
            elif weekly_change > 0:
                trend = 'up'
                trend_text = f'↑{weekly_change}'
            else:
                trend = 'down'
                trend_text = f'↓{abs(weekly_change)}'
            
            equipment_data = {
                'id': f'equipment_{equipment_num:03d}',
                'name': f'{equipment_type} {equipment_num}',
                'type': equipment_type,
                'category': category,
                'total_minutes': base_minutes,
                'weekly_change': weekly_change,
                'trend': trend,
                'trend_text': trend_text,
                'peak_hours': random.choice(['5-8pm', '6-9am', '12-2pm', '7-9pm', '6-8pm', '--']),
                'report_period': 'Week ending Aug 18, 2025'
            }
            equipment_list.append(equipment_data)
        
        # Sort by total minutes (highest first)
        equipment_list.sort(key=lambda x: x['total_minutes'], reverse=True)
        
        return equipment_list
    
    def get_summary_stats(self):
        """Calculate summary statistics from equipment data"""
        if not self.equipment_data:
            return {}
        
        total_minutes = sum(item['total_minutes'] for item in self.equipment_data)
        avg_minutes = round(total_minutes / len(self.equipment_data))
        
        # Top and bottom performers for summary tab
        top_performers = sorted(self.equipment_data, key=lambda x: x['total_minutes'], reverse=True)[:3]
        bottom_performers = sorted(self.equipment_data, key=lambda x: x['total_minutes'])[:3]
        
        # Equipment with biggest changes
        trending_up = sorted([item for item in self.equipment_data if item['trend'] == 'up'], 
                           key=lambda x: x['weekly_change'], reverse=True)[:3]
        trending_down = sorted([item for item in self.equipment_data if item['trend'] == 'down'], 
                             key=lambda x: x['weekly_change'])[:3]
        
        return {
            'total_equipment': len(self.equipment_data),
            'avg_minutes_per_machine': avg_minutes,
            'total_weekly_minutes': total_minutes,
            'top_performers': top_performers,
            'bottom_performers': bottom_performers,  # For replacement candidates
            'trending_up': trending_up,
            'trending_down': trending_down
        }
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard with summary and equipment list tabs"""
            stats = self.get_summary_stats()
            return render_template('dashboard.html', stats=stats)
        
        @self.app.route('/api/equipment')
        def api_equipment():
            """Get all equipment data for the equipment list tab"""
            return jsonify({
                'success': True,
                'equipment': self.equipment_data,
                'total_count': len(self.equipment_data),
                'report_period': 'Week ending Aug 18, 2025'
            })
        
        @self.app.route('/api/summary')
        def api_summary():
            """Get summary statistics for the summary tab"""
            stats = self.get_summary_stats()
            return jsonify({
                'success': True,
                'stats': stats
            })
    
    def run(self, host='0.0.0.0', port=8080, debug=False):
        """Run the Flask server"""
        print(f"Starting FloorIQ Dashboard on http://{host}:{port}")
        print(f"📊 Summary tab: Beautiful analytics dashboard")
        print(f"📋 Equipment List tab: Complete equipment performance list")
        self.app.run(host=host, port=port, debug=debug, threaded=True)


def main():
    """Main entry point"""
    app = FloorIQApp()
    app.run(host='0.0.0.0', port=8080, debug=False)


if __name__ == '__main__':
    main()
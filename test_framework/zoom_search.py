#!/usr/bin/env python3
"""
Zoom-in Search Module for Phase B Round 2

This module provides functionality to intelligently zoom into optimal configurations:
1. For Fixed models: Find midpoint between best and neighbor configurations
2. For VAD/Adaptive models: Zoom into most sensitive parameter with proper discrete/continuous handling
"""

import re
import numpy as np
from pathlib import Path

class ZoomSearch:
    def __init__(self):
        # Define step sizes for different parameter types
        self.step_sizes = {
            'chunk_size': 0.5,
            'aggressiveness': 1,
            'starting_aggressiveness': 1,
            'frame_duration_ms': 5,
            'max_silence_frames': 2
        }
        
        # Define valid ranges for parameters
        self.valid_ranges = {
            'chunk_size': (0.1, 10.0),
            'aggressiveness': (0, 3),
            'starting_aggressiveness': (0, 3),
            'frame_duration_ms': (10, 30),
            'max_silence_frames': (1, 30)
        }

    def find_most_sensitive_knob(self, config_averages):
        """Find the most sensitive parameter by analyzing WER variance across parameter ranges"""
        if not config_averages or len(config_averages) < 2:
            print("Not enough configurations to determine sensitive knob")
            return None
        
        # If we only have 2 configs, just pick the first parameter we can find
        if len(config_averages) == 2:
            for config, metrics in config_averages:
                if metrics['avg_wer'] is None:
                    continue
                    
                config_lower = config.lower()
                
                # Try to find any parameter
                if 'chunk' in config_lower:
                    return 'chunk_size'
                elif 'vad' in config_lower and 'adaptive' not in config_lower:
                    return 'aggressiveness'
                elif 'adaptive' in config_lower:
                    return 'starting_aggressiveness'
            
            return None
        
        # Extract parameter values and WER scores
        param_analysis = {
            'chunk_size': [],
            'aggressiveness': [],
            'frame_duration_ms': [],
            'max_silence_frames': [],
            'starting_aggressiveness': []
        }
        
        for config, metrics in config_averages:
            if metrics['avg_wer'] is None:
                continue
                
            # Parse config description to extract parameters
            config_lower = config.lower()
            
            # Extract chunk_size for fixed models
            if 'chunk' in config_lower:
                chunk_match = re.search(r'(\d+\.?\d*)s?\s*chunk', config_lower)
                if chunk_match:
                    param_analysis['chunk_size'].append((float(chunk_match.group(1)), metrics['avg_wer']))
            
            # Extract aggressiveness for VAD models
            if 'vad' in config_lower and 'adaptive' not in config_lower:
                agg_match = re.search(r'\((\d+)/', config_lower)
                if agg_match:
                    param_analysis['aggressiveness'].append((int(agg_match.group(1)), metrics['avg_wer']))
            
            # Extract frame_duration_ms
            frame_match = re.search(r'(\d+)ms', config_lower)
            if frame_match:
                param_analysis['frame_duration_ms'].append((int(frame_match.group(1)), metrics['avg_wer']))
            
            # Extract max_silence_frames
            silence_match = re.search(r'(\d+)\s*frames?', config_lower)
            if silence_match:
                param_analysis['max_silence_frames'].append((int(silence_match.group(1)), metrics['avg_wer']))
            
            # Extract starting_aggressiveness for adaptive models
            if 'adaptive' in config_lower:
                start_agg_match = re.search(r'\((\d+)/', config_lower)
                if start_agg_match:
                    param_analysis['starting_aggressiveness'].append((int(start_agg_match.group(1)), metrics['avg_wer']))
        
        # Calculate variance for each parameter
        param_variance = {}
        for param_name, values in param_analysis.items():
            if len(values) >= 2:
                # Calculate coefficient of variation (std/mean) for WER
                wers = [v[1] for v in values]
                mean_wer = np.mean(wers)
                std_wer = np.std(wers)
                if mean_wer > 0:
                    param_variance[param_name] = std_wer / mean_wer
        
        if not param_variance:
            print("Could not determine parameter sensitivity")
            return None
        
        # Find parameter with highest variance
        most_sensitive = max(param_variance.items(), key=lambda x: x[1])
        print(f"Most sensitive parameter: {most_sensitive[0]} (CV: {most_sensitive[1]:.3f})")
        
        return most_sensitive[0]

    def parse_config_description(self, config_desc, model_type):
        """Parse configuration description to extract parameter values"""
        params = {}
        
        config_lower = config_desc.lower()
        
        if model_type == 'fixed':
            chunk_match = re.search(r'(\d+\.?\d*)s?\s*chunk', config_lower)
            if chunk_match:
                params['chunk_size'] = float(chunk_match.group(1))
        
        elif model_type == 'vad':
            # Extract VAD parameters
            agg_match = re.search(r'\((\d+)/', config_lower)
            if agg_match:
                params['aggressiveness'] = int(agg_match.group(1))
            
            frame_match = re.search(r'(\d+)ms', config_lower)
            if frame_match:
                params['frame_duration_ms'] = int(frame_match.group(1))
            
            silence_match = re.search(r'(\d+)\s*frames?', config_lower)
            if silence_match:
                params['max_silence_frames'] = int(silence_match.group(1))
        
        elif model_type == 'adaptive':
            # Extract adaptive parameters
            start_agg_match = re.search(r'\((\d+)/', config_lower)
            if start_agg_match:
                params['starting_aggressiveness'] = int(start_agg_match.group(1))
            
            frame_match = re.search(r'(\d+)ms', config_lower)
            if frame_match:
                params['frame_duration_ms'] = int(frame_match.group(1))
            
            silence_match = re.search(r'(\d+)\s*frames?', config_lower)
            if silence_match:
                params['max_silence_frames'] = int(silence_match.group(1))
        
        return params

    def create_config_from_params(self, params, model_type):
        """Create a configuration dictionary from parameter values"""
        if model_type == 'fixed':
            if 'chunk_size' in params:
                return {
                    'chunk_size': params['chunk_size'],
                    'description': f'FIXED ({params["chunk_size"]}s chunks)'
                }
        
        elif model_type == 'vad':
            if all(k in params for k in ['aggressiveness', 'frame_duration_ms', 'max_silence_frames']):
                return {
                    'aggressiveness': params['aggressiveness'],
                    'frame_duration_ms': params['frame_duration_ms'],
                    'max_silence_frames': params['max_silence_frames'],
                    'description': f'VAD ({params["aggressiveness"]}/{params["frame_duration_ms"]}ms/{params["max_silence_frames"]} frames)'
                }
        
        elif model_type == 'adaptive':
            if all(k in params for k in ['starting_aggressiveness', 'frame_duration_ms', 'max_silence_frames']):
                return {
                    'starting_aggressiveness': params['starting_aggressiveness'],
                    'frame_duration_ms': params['frame_duration_ms'],
                    'max_silence_frames': params['max_silence_frames'],
                    'description': f'ADAPTIVE ({params["starting_aggressiveness"]}/{params["frame_duration_ms"]}ms/{params["max_silence_frames"]} frames)'
                }
        
        return None

    def run_zoom_in_search(self, config_averages, model_type):
        """Run zoom-in search based on model type and parameter sensitivity"""
        print(f"\nStarting zoom-in search for {model_type} model...")
        
        if not config_averages:
            print("No configuration data available for zoom-in search")
            return []
        
        if model_type == 'fixed':
            return self._zoom_search_fixed(config_averages)
        else:
            return self._zoom_search_vad_adaptive(config_averages, model_type)

    def _zoom_search_fixed(self, config_averages):
        """Zoom search for fixed models - simple midpoint between best and neighbor"""
        if len(config_averages) < 2:
            print("Need at least 2 configurations for fixed zoom search")
            return []
        
        # Sort by WER (best first)
        sorted_configs = sorted(config_averages, key=lambda x: x[1]['avg_wer'])
        best_config, best_metrics = sorted_configs[0]
        
        # Find the closest neighbor (next best)
        neighbor_config, neighbor_metrics = sorted_configs[1]
        
        # Extract chunk sizes
        best_params = self.parse_config_description(best_config, 'fixed')
        neighbor_params = self.parse_config_description(neighbor_config, 'fixed')
        
        if not best_params or not neighbor_params or 'chunk_size' not in best_params or 'chunk_size' not in neighbor_params:
            print("Could not extract chunk sizes from configurations")
            return []
        
        best_chunk = best_params['chunk_size']
        neighbor_chunk = neighbor_params['chunk_size']
        
        # Calculate midpoint
        midpoint_chunk = (best_chunk + neighbor_chunk) / 2
        midpoint_chunk = round(midpoint_chunk, 1)  # Round to 0.1s
        
        print(f"Best config: {best_chunk}s chunks (WER: {best_metrics['avg_wer']:.3f})")
        print(f"Neighbor config: {neighbor_chunk}s chunks (WER: {neighbor_metrics['avg_wer']:.3f})")
        print(f"Testing midpoint: {midpoint_chunk}s chunks")
        
        # Create midpoint configuration
        midpoint_config = {
            'chunk_size': midpoint_chunk,
            'description': f'FIXED ({midpoint_chunk}s chunks)'
        }
        
        return [midpoint_config]

    def _zoom_search_vad_adaptive(self, config_averages, model_type):
        """Zoom search for VAD/Adaptive models - zoom into most sensitive parameter"""
        if len(config_averages) < 2:
            print("Need at least 2 configurations for VAD/Adaptive zoom search")
            return []
        
        # Find most sensitive parameter
        most_sensitive = self.find_most_sensitive_knob(config_averages)
        if not most_sensitive:
            print("Could not determine most sensitive parameter")
            return []
        
        print(f"Most sensitive parameter: {most_sensitive}")
        
        # Get best configuration
        sorted_configs = sorted(config_averages, key=lambda x: x[1]['avg_wer'])
        best_config, best_metrics = sorted_configs[0]
        best_params = self.parse_config_description(best_config, model_type)
        
        if not best_params:
            print("Could not parse best configuration parameters")
            return []
        
        # Determine zoom strategy based on parameter type
        if most_sensitive == 'aggressiveness' or most_sensitive == 'starting_aggressiveness':
            return self._zoom_search_discrete_param(config_averages, model_type, most_sensitive, best_params)
        else:
            return self._zoom_search_continuous_param(config_averages, model_type, most_sensitive, best_params)

    def _zoom_search_continuous_param(self, config_averages, model_type, param_name, best_params):
        """Zoom search for continuous parameters (frame_duration_ms, max_silence_frames)"""
        current_value = best_params.get(param_name)
        if current_value is None:
            print(f"Could not find {param_name} in best configuration")
            return []
        
        # Find all values for this parameter
        all_values = set()
        for config, _ in config_averages:
            params = self.parse_config_description(config, model_type)
            if params and param_name in params:
                all_values.add(params[param_name])
        
        # Find closest neighbor
        neighbor_values = [v for v in all_values if v != current_value]
        if not neighbor_values:
            print(f"No neighbor values found for {param_name}")
            return []
        
        closest_neighbor = min(neighbor_values, key=lambda x: abs(x - current_value))
        
        print(f"Current {param_name}: {current_value}")
        print(f"Closest neighbor {param_name}: {closest_neighbor}")
        
        # Generate ONLY the midpoint between current and closest neighbor
        midpoint_value = (current_value + closest_neighbor) / 2
        midpoint_value = int(round(midpoint_value))  # Round to nearest integer
        
        min_val, max_val = self.valid_ranges.get(param_name, (0, 100))
        if min_val <= midpoint_value <= max_val:
            midpoint_params = best_params.copy()
            midpoint_params[param_name] = midpoint_value
            
            midpoint_config = self.create_config_from_params(midpoint_params, model_type)
            if midpoint_config:
                print(f"Generated midpoint configuration: {midpoint_config['description']}")
                return [midpoint_config]
        
        print("Could not generate valid midpoint configuration")
        return []

    def _zoom_search_discrete_param(self, config_averages, model_type, param_name, best_params):
        """Zoom search for discrete parameters (aggressiveness)"""
        current_value = best_params.get(param_name)
        if current_value is None:
            print(f"Could not find {param_name} in best configuration")
            return []
        
        # Check if we have enough space for meaningful neighbors
        # For aggressiveness: 0,1,2,3 - need at least 2 steps difference
        all_values = set()
        for config, _ in config_averages:
            params = self.parse_config_description(config, model_type)
            if params and param_name in params:
                all_values.add(params[param_name])
        
        # Find the closest neighbor value
        neighbor_values = []
        for value in all_values:
            if value != current_value:
                neighbor_values.append(value)
        
        if not neighbor_values:
            print(f"No neighbor values found for {param_name}")
            return []
        
        # Find closest neighbor
        closest_neighbor = min(neighbor_values, key=lambda x: abs(x - current_value))
        difference = abs(closest_neighbor - current_value)
        
        print(f"Current {param_name}: {current_value}")
        print(f"Closest neighbor {param_name}: {closest_neighbor} (difference: {difference})")
        
        # Only proceed if difference is at least 2 (for meaningful midpoint)
        if difference < 2:
            print(f"Difference too small ({difference}) for {param_name}, falling back to frame_duration_ms")
            return self._zoom_search_continuous_param(config_averages, model_type, 'frame_duration_ms', best_params)
        
        # Generate ONLY the midpoint between current and closest neighbor
        midpoint_value = (current_value + closest_neighbor) / 2
        midpoint_value = int(round(midpoint_value))  # Round to nearest integer
        
        if 0 <= midpoint_value <= 3:
            midpoint_params = best_params.copy()
            midpoint_params[param_name] = midpoint_value
            
            midpoint_config = self.create_config_from_params(midpoint_params, model_type)
            if midpoint_config:
                print(f"Generated midpoint configuration: {midpoint_config['description']}")
                return [midpoint_config]
        
        print("Could not generate valid midpoint configuration")
        return [] 
#!/usr/bin/env python3
"""
Simplified Zoom Search for ASR Configuration Optimization

This module implements a simple zoom search that:
1. Picks the best 2 configs from each model type
2. Finds midpoints for the most sensitive parameters
3. Returns new configs for testing
"""

from typing import List, Dict, Tuple
import math

class ZoomSearch:
    def __init__(self):
        pass
    
    def run_zoom_search(self, results_data: List[Dict], model_type: str) -> List[Dict]:
        """
        Run simplified zoom search for a specific model type
        
        Args:
            results_data: List of test results from previous phase
            model_type: 'fixed', 'vad', or 'adaptive'
            
        Returns:
            List of new configs to test (midpoint configs)
        """
        print(f"🔍 Running zoom search for {model_type} model...")
        
        # Get best 2 configs for this model type
        best_configs = self._get_best_2_configs(results_data, model_type)
        
        if len(best_configs) < 2:
            print(f"⚠️  Only {len(best_configs)} configs available for {model_type}, skipping zoom search")
            return []
        
        # Generate midpoint configs
        midpoint_configs = self._generate_midpoint_configs(best_configs, model_type)
        
        print(f"✅ Generated {len(midpoint_configs)} midpoint configs for {model_type}")
        return midpoint_configs
    
    def _get_best_2_configs(self, results_data: List[Dict], model_type: str) -> List[Dict]:
        """Get the best 2 configs for a specific model type"""
        # Filter results by model type
        model_results = [r for r in results_data if r.get('model_type') == model_type]
        
        if not model_results:
            return []
        
        # Calculate averages for each config
        config_averages = self._calculate_config_averages(model_results)
        
        # Sort by WER, then by p90 latency
        config_averages.sort(key=lambda x: (
            x[1]['avg_wer'] if x[1]['avg_wer'] is not None else float('inf'),
            x[1]['avg_p90_latency']
        ))
        
        # Get best 2 configs
        best_2 = config_averages[:2]
        
        # Extract the config objects (not just descriptions)
        best_configs = []
        for config_desc, metrics in best_2:
            # Find the original config object
            for result in model_results:
                if result.get('config') == config_desc:
                    # Reconstruct config from result data
                    config = self._reconstruct_config_from_result(result)
                    if config:
                        best_configs.append(config)
                    break
        
        return best_configs
    
    def _generate_midpoint_configs(self, best_configs: List[Dict], model_type: str) -> List[Dict]:
        """Generate midpoint configs based on model type"""
        if len(best_configs) < 2:
            return []
        
        config1, config2 = best_configs[0], best_configs[1]
        
        if model_type == 'fixed':
            return self._generate_fixed_midpoint(config1, config2)
        elif model_type in ['vad', 'adaptive']:
            return self._generate_vad_midpoint(config1, config2)
        else:
            return []
    
    def _generate_fixed_midpoint(self, config1: Dict, config2: Dict) -> List[Dict]:
        """Generate midpoint for fixed chunking (chunk_size)"""
        chunk_size1 = config1.get('chunk_size', 0)
        chunk_size2 = config2.get('chunk_size', 0)
        
        # Find midpoint
        midpoint_chunk_size = (chunk_size1 + chunk_size2) / 2
        midpoint_chunk_size = round(midpoint_chunk_size, 1)  # Round to 1 decimal place
        
        # Create midpoint config
        midpoint_config = config1.copy()
        midpoint_config['chunk_size'] = midpoint_chunk_size
        midpoint_config['model_type'] = 'fixed'  # Ensure model_type is set
        midpoint_config['description'] = f"ZOOM-MIDPOINT: chunk_size={midpoint_chunk_size}s (between {chunk_size1}s and {chunk_size2}s)"
        
        print(f"   📏 Fixed midpoint: chunk_size = {midpoint_chunk_size}s (between {chunk_size1}s and {chunk_size2}s)")
        return [midpoint_config]
    
    def _generate_vad_midpoint(self, config1: Dict, config2: Dict) -> List[Dict]:
        """Generate midpoint for VAD/Adaptive (frames as most sensitive)"""
        frames1 = config1.get('max_silence_frames', 0)
        frames2 = config2.get('max_silence_frames', 0)
        
        # Find midpoint of frames
        midpoint_frames = (frames1 + frames2) / 2
        midpoint_frames = int(round(midpoint_frames))  # Round to integer
        
        # Create midpoint config
        midpoint_config = config1.copy()
        midpoint_config['max_silence_frames'] = midpoint_frames
        # Ensure model_type is set (use the original model_type from config1)
        midpoint_config['model_type'] = config1.get('model_type', 'vad')
        midpoint_config['description'] = f"ZOOM-MIDPOINT: frames={midpoint_frames} (between {frames1} and {frames2})"
        
        print(f"   📏 VAD/Adaptive midpoint: frames = {midpoint_frames} (between {frames1} and {frames2})")
        return [midpoint_config]
    
    def _calculate_config_averages(self, results: List[Dict]) -> List[Tuple[str, Dict]]:
        """Calculate averages for each configuration"""
        config_groups = {}
        
        # Group results by configuration
        for result in results:
            config = result['config']
            if config not in config_groups:
                config_groups[config] = []
            config_groups[config].append(result)
        
        # Calculate averages for each configuration
        config_averages = []
        for config, runs in config_groups.items():
            if not runs:
                continue
                
            # Calculate averages
            avg_wer = None
            wer_scores = [r['wer_score'] for r in runs if r['wer_score'] is not None]
            if wer_scores:
                avg_wer = sum(wer_scores) / len(wer_scores)
            
            avg_p90_latency = sum(r['p90_processing_latency'] for r in runs) / len(runs)
            
            config_averages.append((config, {
                'avg_wer': avg_wer,
                'avg_p90_latency': avg_p90_latency
            }))
        
        return config_averages
    
    def _reconstruct_config_from_result(self, result: Dict) -> Dict:
        """Reconstruct config object from result data"""
        # Extract config parameters from result
        config = {}
        
        # Common parameters
        if 'model_type' in result:
            config['model_type'] = result['model_type']
        
        # Fixed chunking parameters
        if result.get('model_type') == 'fixed':
            # Extract chunk_size from description like "FIXED-Sobol-7 (2.8s)"
            desc = result.get('config', '')
            if '(' in desc and 's)' in desc:
                try:
                    chunk_size_str = desc.split('(')[1].split('s)')[0]
                    config['chunk_size'] = float(chunk_size_str)
                except:
                    config['chunk_size'] = 2.0  # fallback
        
        # VAD/Adaptive parameters
        elif result.get('model_type') in ['vad', 'adaptive']:
            # Extract parameters from description like "Sobol-9: agg=0, frames=9"
            desc = result.get('config', '')
            if 'agg=' in desc and 'frames=' in desc:
                try:
                    agg_str = desc.split('agg=')[1].split(',')[0]
                    frames_str = desc.split('frames=')[1].split()[0]
                    config['aggressiveness'] = int(agg_str)
                    config['max_silence_frames'] = int(frames_str)
                    config['frame_duration_ms'] = 20  # default
                except:
                    config['aggressiveness'] = 1
                    config['max_silence_frames'] = 10
                    config['frame_duration_ms'] = 20
        
        # Adaptive-specific parameters
        if result.get('model_type') == 'adaptive':
            config['starting_aggressiveness'] = config.get('aggressiveness', 1)
        
        config['description'] = result.get('config', 'Unknown')
        
        return config 
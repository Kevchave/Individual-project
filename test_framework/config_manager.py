#!/usr/bin/env python3
"""
Configuration Manager for Automatic Configuration Evolution

This module handles the automatic evolution of configurations through testing phases:
- Phase A Round 1: All configs from configs.py
- Phase A Round 2: Top 50% from A1 results
- Phase B Round 1: Top 2/3 from A2 results
- Phase B Round 2: Zoom search around best from B1
- Phase C: Best config from B2
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from configs import TEST_CONFIGS

class ConfigManager:
    def __init__(self, registry_dir="config_registry"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(exist_ok=True)
        
        # Define phase evolution rules
        self.evolution_rules = {
            'phase_a_r1': {
                'source': 'configs.py',
                'description': 'All initial configurations from configs.py'
            },
            'phase_a_r2': {
                'source': 'phase_a_r1',
                'selection': 'top_50_percent',
                'description': 'Top 50% configurations from Phase A Round 1'
            },
            'phase_b_r1': {
                'source': 'phase_a_r2',
                'selection': 'best_2_fixed_3_vad_adaptive',
                'description': 'Best 2 from fixed, best 3 from VAD, best 3 from adaptive (8 total)'
            },
            'phase_b_r2': {
                'source': 'phase_b_r1',
                'selection': 'zoom_search',
                'description': 'Zoom search configurations around best from Phase B Round 1'
            },
            'phase_c': {
                'source': 'phase_b_r2',
                'selection': 'best_config',
                'description': 'Best configuration from Phase B Round 2'
            }
        }
    
    def initialize_phase_a_r1(self, model_type: str) -> bool:
        """Initialize Phase A Round 1 configurations from configs.py"""
        if model_type == 'combined':
            # Initialize all model types for combined approach
            success = True
            for mt in ['fixed', 'vad', 'adaptive']:
                if not self.initialize_phase_a_r1(mt):
                    success = False
            return success
        
        # Load configs from configs.py
        if model_type not in TEST_CONFIGS:
            print(f"Error: Unknown model type '{model_type}'")
            return False
        
        configs = TEST_CONFIGS[model_type]
        
        # Save to registry
        config_file = self.registry_dir / f"{model_type}_phase_a_r1_configs.json"
        data = {
            'model_type': model_type,
            'phase': 'phase_a_r1',
            'source': 'configs.py',
            'generated_at': datetime.now().isoformat(),
            'description': 'All initial configurations from configs.py',
            'configs': configs
        }
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Initialized Phase A Round 1 configs for {model_type}: {len(configs)} configurations")
        return True
    
    def evolve_configs(self, source_phase: str, target_phase: str, model_type: str, 
                      results_data: List[Dict], zoom_search_results: Optional[List] = None) -> bool:
        """Evolve configurations from source phase to target phase"""
        
        if target_phase not in self.evolution_rules:
            print(f"Error: Unknown target phase '{target_phase}'")
            return False
        
        rule = self.evolution_rules[target_phase]
        
        if rule['source'] == 'configs.py':
            return self.initialize_phase_a_r1(model_type)
        
        # Get source configs
        source_configs = self.load_phase_configs(model_type, rule['source'])
        if not source_configs:
            print(f"Error: Could not load source configs for {rule['source']}")
            return False
        
        # Apply selection criteria
        if rule['selection'] == 'top_50_percent':
            selected_configs = self._select_top_percent(results_data, source_configs, 50)
        elif rule['selection'] == 'best_2_fixed_3_vad_adaptive':
            selected_configs = self._select_best_2_fixed_3_vad_adaptive(results_data, source_configs)
        elif rule['selection'] == 'zoom_search':
            selected_configs = self._apply_zoom_search(results_data, source_configs, zoom_search_results)
        elif rule['selection'] == 'best_config':
            selected_configs = self._select_best_config(results_data, source_configs)
        else:
            print(f"Error: Unknown selection criteria '{rule['selection']}'")
            return False
        
        # Save evolved configs
        config_data = {
            'model_type': model_type,
            'phase': target_phase,
            'source': rule['source'],
            'selection_criteria': rule['selection'],
            'generated_at': datetime.now().isoformat(),
            'description': rule['description'],
            'configs': selected_configs,
            'metadata': {
                'source_phase': rule['source'],
                'total_configs': len(selected_configs),
                'selection_criteria': rule['selection']
            }
        }
        
        if model_type == 'combined':
            # Save separate files for each model type
            # IMPORTANT: selected_configs are already in the correct sorted order from the selection method
            # We need to preserve this order when separating by model type
            fixed_configs = []
            vad_configs = []
            adaptive_configs = []
            
            # Process configs in the order they appear in selected_configs (which is already sorted)
            for config in selected_configs:
                # For zoom search configs, use the model_type field directly
                if config.get('description', '').startswith('ZOOM-MIDPOINT:'):
                    model_type_from_config = config.get('model_type')
                    if model_type_from_config:
                        if model_type_from_config == 'fixed':
                            fixed_configs.append(config)
                        elif model_type_from_config == 'vad':
                            vad_configs.append(config)
                        elif model_type_from_config == 'adaptive':
                            adaptive_configs.append(config)
                    continue
                
                # For regular configs, find the corresponding result to get the model_type
                model_type_from_result = None
                for result in results_data:
                    if result.get('config') == config.get('description'):
                        model_type_from_result = result.get('model_type')
                        break
                
                # Fallback to description parsing if model_type not found
                if not model_type_from_result:
                    desc_lower = config.get('description', '').lower()
                    if 'fixed' in desc_lower:
                        model_type_from_result = 'fixed'
                    elif 'vad' in desc_lower and 'adaptive' not in desc_lower:
                        model_type_from_result = 'vad'
                    elif 'adaptive' in desc_lower:
                        model_type_from_result = 'adaptive'
                
                # Add to appropriate list (maintaining the sorted order from selected_configs)
                if model_type_from_result == 'fixed':
                    fixed_configs.append(config)
                elif model_type_from_result == 'vad':
                    vad_configs.append(config)
                elif model_type_from_result == 'adaptive':
                    adaptive_configs.append(config)
            
            # Save fixed configs
            if fixed_configs:
                fixed_data = config_data.copy()
                fixed_data['model_type'] = 'fixed'
                fixed_data['configs'] = fixed_configs
                fixed_file = self.registry_dir / f"fixed_{target_phase}_configs.json"
                with open(fixed_file, 'w') as f:
                    json.dump(fixed_data, f, indent=2)
            
            # Save VAD configs
            if vad_configs:
                vad_data = config_data.copy()
                vad_data['model_type'] = 'vad'
                vad_data['configs'] = vad_configs
                vad_file = self.registry_dir / f"vad_{target_phase}_configs.json"
                with open(vad_file, 'w') as f:
                    json.dump(vad_data, f, indent=2)
            
            # Save adaptive configs
            if adaptive_configs:
                adaptive_data = config_data.copy()
                adaptive_data['model_type'] = 'adaptive'
                adaptive_data['configs'] = adaptive_configs
                adaptive_file = self.registry_dir / f"adaptive_{target_phase}_configs.json"
                with open(adaptive_file, 'w') as f:
                    json.dump(adaptive_data, f, indent=2)
        else:
            # Save single file for individual model type
            config_file = self.registry_dir / f"{model_type}_{target_phase}_configs.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        
        print(f"Evolved configs for {target_phase}: {len(selected_configs)} configurations")
        return True
    
    def load_phase_configs(self, model_type: str, phase: str) -> Optional[List[Dict]]:
        """Load configurations for a specific phase and model type"""
        if model_type == 'combined':
            # Load from all model types for combined approach
            all_configs = []
            for mt in ['fixed', 'vad', 'adaptive']:
                configs = self.load_phase_configs(mt, phase)
                if configs:
                    all_configs.extend(configs)
            return all_configs
        
        config_file = self.registry_dir / f"{model_type}_{phase}_configs.json"
        
        if not config_file.exists():
            print(f"Config file not found: {config_file}")
            return None
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            
            return data.get('configs', [])
        except Exception as e:
            print(f"Error loading config file {config_file}: {e}")
            return None
    
    def get_phase_configs(self, model_type: str, phase: str) -> Optional[List[Dict]]:
        """Get configurations for a specific phase (public interface)"""
        return self.load_phase_configs(model_type, phase)
    
    def _select_top_percent(self, results_data: List[Dict], source_configs: List[Dict], 
                           percent: float) -> List[Dict]:
        """Select top N% configurations from each model type independently"""
        # Calculate configuration averages
        config_averages = self._calculate_config_averages(results_data)
        
        if not config_averages:
            return source_configs
        
        # Separate configs by model type
        fixed_configs = []
        vad_configs = []
        adaptive_configs = []
        
        for config_desc, metrics in config_averages:
            # Find matching config in source_configs
            for config in source_configs:
                if config.get('description') == config_desc:
                    # Use model_type from results data instead of parsing description
                    # Find the corresponding result to get the model_type
                    model_type = None
                    for result in results_data:
                        if result.get('config') == config_desc:
                            model_type = result.get('model_type')
                            break
                    
                    # Fallback to description parsing if model_type not found
                    if not model_type:
                        desc_lower = config_desc.lower()
                        if 'fixed' in desc_lower:
                            model_type = 'fixed'
                        elif 'vad' in desc_lower and 'adaptive' not in desc_lower:
                            model_type = 'vad'
                        elif 'adaptive' in desc_lower:
                            model_type = 'adaptive'
                    
                    # Add to appropriate list
                    if model_type == 'fixed':
                        fixed_configs.append((config_desc, metrics, config))
                    elif model_type == 'vad':
                        vad_configs.append((config_desc, metrics, config))
                    elif model_type == 'adaptive':
                        adaptive_configs.append((config_desc, metrics, config))
                    break
        
        # Sort each group by WER, then by p90 latency
        def sort_key(item):
            config_desc, metrics, config = item
            return (
                metrics['avg_wer'] if metrics['avg_wer'] is not None else float('inf'),
                metrics['avg_p90_latency']
            )
        
        fixed_configs.sort(key=sort_key)
        vad_configs.sort(key=sort_key)
        adaptive_configs.sort(key=sort_key)
        
        # Select top N% from each model type independently
        target_fixed = max(1, int(len(fixed_configs) * percent / 100))
        target_vad = max(1, int(len(vad_configs) * percent / 100))
        target_adaptive = max(1, int(len(adaptive_configs) * percent / 100))
        
        # Select top configs from each group
        selected_configs = []
        
        # Best configs from fixed
        for _, _, config in fixed_configs[:target_fixed]:
            selected_configs.append(config)
        
        # Best configs from VAD
        for _, _, config in vad_configs[:target_vad]:
            selected_configs.append(config)
        
        # Best configs from adaptive
        for _, _, config in adaptive_configs[:target_adaptive]:
            selected_configs.append(config)
        
        print(f"Selected: {target_fixed} fixed, {target_vad} VAD, {target_adaptive} adaptive "
              f"(Available: {len(fixed_configs)}/{len(vad_configs)}/{len(adaptive_configs)}, Total: {len(selected_configs)})")
        
        return selected_configs
    
    def _select_best_2_fixed_3_vad_adaptive(self, results_data: List[Dict], source_configs: List[Dict]) -> List[Dict]:
        """Select best 2 from fixed, best 3 from VAD, best 3 from adaptive"""
        # Calculate configuration averages
        config_averages = self._calculate_config_averages(results_data)
        
        if not config_averages:
            return source_configs
        
        # Separate configs by model type
        fixed_configs = []
        vad_configs = []
        adaptive_configs = []
        
        for config_desc, metrics in config_averages:
            # Find matching config in source_configs
            for config in source_configs:
                if config.get('description') == config_desc:
                    # Use model_type from results data instead of parsing description
                    # Find the corresponding result to get the model_type
                    model_type = None
                    for result in results_data:
                        if result.get('config') == config_desc:
                            model_type = result.get('model_type')
                            break
                    
                    # Fallback to description parsing if model_type not found
                    if not model_type:
                        desc_lower = config_desc.lower()
                        if 'fixed' in desc_lower:
                            model_type = 'fixed'
                        elif 'vad' in desc_lower and 'adaptive' not in desc_lower:
                            model_type = 'vad'
                        elif 'adaptive' in desc_lower:
                            model_type = 'adaptive'
                    
                    # Add to appropriate list
                    if model_type == 'fixed':
                        fixed_configs.append((config_desc, metrics, config))
                    elif model_type == 'vad':
                        vad_configs.append((config_desc, metrics, config))
                    elif model_type == 'adaptive':
                        adaptive_configs.append((config_desc, metrics, config))
                    break
        
        # Sort each group by WER, then by p90 latency
        def sort_key(item):
            config_desc, metrics, config = item
            return (
                metrics['avg_wer'] if metrics['avg_wer'] is not None else float('inf'),
                metrics['avg_p90_latency']
            )
        
        fixed_configs.sort(key=sort_key)
        vad_configs.sort(key=sort_key)
        adaptive_configs.sort(key=sort_key)
        
        # Select top configs from each group (always pick target numbers)
        selected_configs = []
        
        # Best 2 from fixed (or all available if fewer than 2)
        target_fixed = min(2, len(fixed_configs))
        for _, _, config in fixed_configs[:target_fixed]:
            selected_configs.append(config)
        
        # Best 3 from VAD (or all available if fewer than 3)
        target_vad = min(3, len(vad_configs))
        for _, _, config in vad_configs[:target_vad]:
            selected_configs.append(config)
        
        # Best 3 from adaptive (or all available if fewer than 3)
        target_adaptive = min(3, len(adaptive_configs))
        for _, _, config in adaptive_configs[:target_adaptive]:
            selected_configs.append(config)
        
        print(f"Selected: {target_fixed} fixed, {target_vad} VAD, {target_adaptive} adaptive "
              f"(Available: {len(fixed_configs)}/{len(vad_configs)}/{len(adaptive_configs)})")
        
        return selected_configs
    
    def _apply_zoom_search(self, results_data: List[Dict], source_configs: List[Dict], 
                           zoom_search_results: List[Dict]) -> List[Dict]:
        """Apply zoom search using the simplified zoom_search.py module"""
        from zoom_search import ZoomSearch
        
        zoom_search = ZoomSearch()
        
        # Run zoom search for each model type
        all_zoom_configs = []
        
        for model_type in ['fixed', 'vad', 'adaptive']:
            # Filter results for this model type
            model_results = [r for r in results_data if r.get('model_type') == model_type]
            
            if model_results:
                zoom_configs = zoom_search.run_zoom_search(model_results, model_type)
                all_zoom_configs.extend(zoom_configs)
        
        if all_zoom_configs:
            print(f"🔍 Zoom search: Generated {len(all_zoom_configs)} new configurations")
            return all_zoom_configs
        else:
            print("⚠️  Zoom search: No new configurations generated")
            return []
    
    def _select_best_config(self, results_data: List[Dict], source_configs: List[Dict]) -> List[Dict]:
        """Select the best configuration based on results"""
        config_averages = self._calculate_config_averages(results_data)
        
        if not config_averages:
            return source_configs[:1] if source_configs else []
        
        # Sort by WER, then by p90 latency
        config_averages.sort(key=lambda x: (
            x[1]['avg_wer'] if x[1]['avg_wer'] is not None else float('inf'),
            x[1]['avg_p90_latency']
        ))
        
        best_config_desc = config_averages[0][0]
        
        # Find matching config in source_configs
        for config in source_configs:
            if config.get('description') == best_config_desc:
                return [config]
        
        return source_configs[:1] if source_configs else []
    
    def _calculate_config_averages(self, results_data: List[Dict]) -> List[tuple]:
        """Calculate average metrics for each configuration"""
        config_groups = {}
        
        # Group results by configuration
        for result in results_data:
            if 'error' in result:
                continue
                
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
            
            avg_latency = sum(r['processing_latency'] for r in runs) / len(runs)
            avg_p90_latency = sum(r['p90_processing_latency'] for r in runs) / len(runs)
            
            config_averages.append((config, {
                'avg_wer': avg_wer,
                'avg_latency': avg_latency,
                'avg_p90_latency': avg_p90_latency,
                'num_runs': len(runs)
            }))
        
        return config_averages
    
    def show_config_evolution(self, model_type: str) -> None:
        """Show how configurations evolved through phases"""
        print(f"\nConfiguration Evolution for {model_type.upper()}")
        print("=" * 60)
        
        for phase in ['phase_a_r1', 'phase_a_r2', 'phase_b_r1', 'phase_b_r2', 'phase_c']:
            configs = self.load_phase_configs(model_type, phase)
            if configs:
                print(f"{phase:12}: {len(configs):2d} configs")
            else:
                print(f"{phase:12}: Not generated yet")
    
    def validate_phase_configs(self, model_type: str, phase: str) -> bool:
        """Validate that phase configs exist and are properly formatted"""
        configs = self.load_phase_configs(model_type, phase)
        if not configs:
            print(f"Error: No configurations found for {model_type} {phase}")
            return False
        
        print(f"✓ Validated {phase}: {len(configs)} configurations")
        return True
    
    def rollback_to_phase(self, model_type: str, target_phase: str) -> bool:
        """Rollback to a specific phase (delete all subsequent phase configs)"""
        phases = ['phase_a_r1', 'phase_a_r2', 'phase_b_r1', 'phase_b_r2', 'phase_c']
        
        try:
            target_index = phases.index(target_phase)
        except ValueError:
            print(f"Error: Invalid phase '{target_phase}'")
            return False
        
        # Delete all phases after target_phase
        for phase in phases[target_index + 1:]:
            config_file = self.registry_dir / f"{model_type}_{phase}_configs.json"
            if config_file.exists():
                config_file.unlink()
                print(f"Deleted {phase} configs")
        
        print(f"Rolled back to {target_phase}")
        return True 
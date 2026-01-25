"""
Version Comparison Service Module
Handles policy version comparison, diff generation, and change analysis
"""
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import difflib

from data_models import Policy
from policy_service import PolicyService
from common_utils import get_timestamp


@dataclass
class RuleChange:
    """Represents a change to a policy rule"""
    rule_id: str
    change_type: str  # 'added', 'removed', 'modified'
    field: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    category: Optional[str] = None  # 'coverage', 'exclusions', 'limits', 'metadata'
    similarity_score: float = 0.0


@dataclass
class VersionComparison:
    """Represents a comparison between two policy versions"""
    policy_id: str
    version1: int
    version2: int
    added_rules: List[Dict[str, Any]]
    removed_rules: List[Dict[str, Any]]
    modified_rules: List[RuleChange]
    unchanged_rules: List[Dict[str, Any]]
    summary: Dict[str, int]
    comparison_timestamp: str


class VersionComparisonService:
    """Service for comparing policy versions"""
    
    def __init__(self, policy_service: PolicyService):
        self.policy_service = policy_service
    
    def compare_versions(
        self,
        hospital_id: str,
        policy_id: str,
        version1: int,
        version2: int
    ) -> VersionComparison:
        """
        Compare two versions of a policy and generate structured diff
        
        Args:
            hospital_id: Hospital identifier
            policy_id: Policy identifier
            version1: First version number
            version2: Second version number
            
        Returns:
            VersionComparison object with detailed diff
        """
        # Get both policy versions
        policy1 = self._get_policy_version(hospital_id, policy_id, version1)
        policy2 = self._get_policy_version(hospital_id, policy_id, version2)
        
        if not policy1 or not policy2:
            raise ValueError(f"Could not find one or both policy versions")
        
        # Extract rules from both versions
        rules1 = policy1.extracted_rules or {}
        rules2 = policy2.extracted_rules or {}
        
        # Compare rules
        added, removed, modified, unchanged = self._compare_rules(rules1, rules2)
        
        # Create summary
        summary = {
            'added': len(added),
            'removed': len(removed),
            'modified': len(modified),
            'unchanged': len(unchanged),
            'total_changes': len(added) + len(removed) + len(modified)
        }
        
        return VersionComparison(
            policy_id=policy_id,
            version1=version1,
            version2=version2,
            added_rules=added,
            removed_rules=removed,
            modified_rules=modified,
            unchanged_rules=unchanged,
            summary=summary,
            comparison_timestamp=get_timestamp()
        )
    
    def _get_policy_version(
        self,
        hospital_id: str,
        policy_id: str,
        version: int
    ) -> Optional[Policy]:
        """
        Get a specific version of a policy
        
        Note: In current implementation, only the latest version is stored.
        For full version history, would need separate versioning table.
        """
        # Get current policy
        policy = self.policy_service.get_policy(hospital_id, policy_id)
        
        if not policy:
            return None
        
        # If requesting current version, return it
        if version == policy.version:
            return policy
        
        # For historical versions, reconstruct from audit trail
        return self._reconstruct_version_from_audit(policy_id, version)
    
    def _reconstruct_version_from_audit(
        self,
        policy_id: str,
        version: int
    ) -> Optional[Policy]:
        """
        Reconstruct a historical policy version from audit trail
        
        Note: This is a simplified implementation. In production,
        you'd want to store full version snapshots.
        """
        audit_trail = self.policy_service.get_policy_audit_trail(policy_id)
        
        # Find the audit entry for this version
        for entry in audit_trail:
            if entry.get('action') in ['CREATE_POLICY', 'UPDATE_POLICY']:
                entry_version = entry.get('changes', {}).get('version')
                if entry_version == version:
                    # Reconstruct policy from after_state
                    after_state = entry.get('after_state', {})
                    if after_state:
                        try:
                            return Policy(**after_state)
                        except Exception:
                            pass
        
        return None
    
    def _compare_rules(
        self,
        rules1: Dict[str, Any],
        rules2: Dict[str, Any]
    ) -> Tuple[List[Dict], List[Dict], List[RuleChange], List[Dict]]:
        """
        Compare two sets of policy rules
        
        Returns:
            Tuple of (added, removed, modified, unchanged) rules
        """
        added = []
        removed = []
        modified = []
        unchanged = []
        
        # Get all rule categories
        all_categories = set(rules1.keys()) | set(rules2.keys())
        
        for category in all_categories:
            cat_rules1 = rules1.get(category)
            cat_rules2 = rules2.get(category)
            
            # Category added
            if cat_rules1 is None and cat_rules2 is not None:
                added.append({
                    'category': category,
                    'value': cat_rules2
                })
                continue
            
            # Category removed
            if cat_rules1 is not None and cat_rules2 is None:
                removed.append({
                    'category': category,
                    'value': cat_rules1
                })
                continue
            
            # Category exists in both - compare values
            if cat_rules1 == cat_rules2:
                unchanged.append({
                    'category': category,
                    'value': cat_rules1
                })
            else:
                # Detect modifications
                changes = self._detect_modifications(
                    category, cat_rules1, cat_rules2
                )
                modified.extend(changes)
        
        return added, removed, modified, unchanged
    
    def _detect_modifications(
        self,
        category: str,
        value1: Any,
        value2: Any
    ) -> List[RuleChange]:
        """
        Detect specific modifications within a category
        """
        changes = []
        
        # Handle dict comparisons
        if isinstance(value1, dict) and isinstance(value2, dict):
            all_keys = set(value1.keys()) | set(value2.keys())
            
            for key in all_keys:
                v1 = value1.get(key)
                v2 = value2.get(key)
                
                if v1 != v2:
                    similarity = self._calculate_similarity(v1, v2)
                    
                    changes.append(RuleChange(
                        rule_id=f"{category}.{key}",
                        change_type='modified',
                        field=key,
                        old_value=v1,
                        new_value=v2,
                        category=self._categorize_rule(category),
                        similarity_score=similarity
                    ))
        
        # Handle list comparisons
        elif isinstance(value1, list) and isinstance(value2, list):
            # Compare list items
            set1 = set(json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item) for item in value1)
            set2 = set(json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item) for item in value2)
            
            if set1 != set2:
                changes.append(RuleChange(
                    rule_id=category,
                    change_type='modified',
                    field=None,
                    old_value=value1,
                    new_value=value2,
                    category=self._categorize_rule(category),
                    similarity_score=self._calculate_list_similarity(value1, value2)
                ))
        
        # Handle simple value comparisons
        else:
            if value1 != value2:
                changes.append(RuleChange(
                    rule_id=category,
                    change_type='modified',
                    field=None,
                    old_value=value1,
                    new_value=value2,
                    category=self._categorize_rule(category),
                    similarity_score=0.0
                ))
        
        return changes
    
    def _calculate_similarity(self, value1: Any, value2: Any) -> float:
        """
        Calculate similarity score between two values (0.0 to 1.0)
        """
        if value1 == value2:
            return 1.0
        
        if value1 is None or value2 is None:
            return 0.0
        
        # For strings, use sequence matcher
        if isinstance(value1, str) and isinstance(value2, str):
            return difflib.SequenceMatcher(None, value1, value2).ratio()
        
        # For numbers, calculate relative difference
        if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            if value1 == 0 and value2 == 0:
                return 1.0
            max_val = max(abs(value1), abs(value2))
            if max_val == 0:
                return 1.0
            diff = abs(value1 - value2)
            return 1.0 - min(diff / max_val, 1.0)
        
        # For other types, just check equality
        return 1.0 if value1 == value2 else 0.0
    
    def _calculate_list_similarity(self, list1: List, list2: List) -> float:
        """
        Calculate similarity between two lists
        """
        if not list1 and not list2:
            return 1.0
        
        if not list1 or not list2:
            return 0.0
        
        # Convert to sets for comparison
        set1 = set(json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item) for item in list1)
        set2 = set(json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item) for item in list2)
        
        # Calculate Jaccard similarity
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _categorize_rule(self, rule_name: str) -> str:
        """
        Categorize a rule into coverage, exclusions, limits, or metadata
        """
        rule_lower = rule_name.lower()
        
        if any(keyword in rule_lower for keyword in ['coverage', 'covered', 'benefit']):
            return 'coverage'
        elif any(keyword in rule_lower for keyword in ['exclusion', 'excluded', 'not_covered']):
            return 'exclusions'
        elif any(keyword in rule_lower for keyword in ['limit', 'cap', 'maximum', 'minimum']):
            return 'limits'
        else:
            return 'metadata'
    
    def generate_diff_report(
        self,
        comparison: VersionComparison
    ) -> Dict[str, Any]:
        """
        Generate a human-readable diff report
        """
        report = {
            'policy_id': comparison.policy_id,
            'versions_compared': f"v{comparison.version1} vs v{comparison.version2}",
            'comparison_date': comparison.comparison_timestamp,
            'summary': comparison.summary,
            'changes_by_category': self._group_changes_by_category(comparison),
            'significant_changes': self._identify_significant_changes(comparison),
            'risk_level': self._assess_change_risk(comparison)
        }
        
        return report
    
    def _group_changes_by_category(
        self,
        comparison: VersionComparison
    ) -> Dict[str, List]:
        """
        Group changes by category (coverage, exclusions, limits, metadata)
        """
        grouped = {
            'coverage': [],
            'exclusions': [],
            'limits': [],
            'metadata': []
        }
        
        # Group added rules
        for rule in comparison.added_rules:
            category = self._categorize_rule(rule.get('category', ''))
            grouped[category].append({
                'type': 'added',
                'rule': rule
            })
        
        # Group removed rules
        for rule in comparison.removed_rules:
            category = self._categorize_rule(rule.get('category', ''))
            grouped[category].append({
                'type': 'removed',
                'rule': rule
            })
        
        # Group modified rules
        for change in comparison.modified_rules:
            category = change.category or 'metadata'
            grouped[category].append({
                'type': 'modified',
                'change': asdict(change)
            })
        
        return grouped
    
    def _identify_significant_changes(
        self,
        comparison: VersionComparison
    ) -> List[Dict[str, Any]]:
        """
        Identify changes that are likely to have significant impact
        """
        significant = []
        
        # Added/removed rules are always significant
        for rule in comparison.added_rules:
            significant.append({
                'type': 'added',
                'category': rule.get('category'),
                'impact': 'high',
                'reason': 'New rule added'
            })
        
        for rule in comparison.removed_rules:
            significant.append({
                'type': 'removed',
                'category': rule.get('category'),
                'impact': 'high',
                'reason': 'Rule removed'
            })
        
        # Modified rules with low similarity are significant
        for change in comparison.modified_rules:
            if change.similarity_score < 0.5:
                significant.append({
                    'type': 'modified',
                    'rule_id': change.rule_id,
                    'category': change.category,
                    'impact': 'high' if change.similarity_score < 0.3 else 'medium',
                    'reason': f'Significant modification (similarity: {change.similarity_score:.2f})'
                })
        
        return significant
    
    def _assess_change_risk(self, comparison: VersionComparison) -> str:
        """
        Assess overall risk level of changes
        """
        total_changes = comparison.summary['total_changes']
        
        if total_changes == 0:
            return 'none'
        elif total_changes <= 3:
            return 'low'
        elif total_changes <= 10:
            return 'medium'
        else:
            return 'high'
    
    def compare_metadata(
        self,
        policy1: Policy,
        policy2: Policy
    ) -> Dict[str, Any]:
        """
        Compare metadata between two policy versions
        """
        metadata_changes = {}
        
        # Compare key metadata fields
        fields_to_compare = [
            'policy_name',
            'effective_date',
            'expiration_date',
            'extraction_confidence',
            'file_size',
            'content_type'
        ]
        
        for field in fields_to_compare:
            val1 = getattr(policy1, field, None)
            val2 = getattr(policy2, field, None)
            
            if val1 != val2:
                metadata_changes[field] = {
                    'old': val1,
                    'new': val2
                }
        
        return metadata_changes

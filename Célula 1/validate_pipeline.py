#!/usr/bin/env python3
"""Validate pipeline.yml CloudFormation template"""

import yaml
import sys

class CFNLoader(yaml.SafeLoader):
    pass

def cfn_constructor(loader, tag_suffix, node):
    """Handle CloudFormation intrinsic functions"""
    if isinstance(node, yaml.ScalarNode):
        return {tag_suffix: loader.construct_scalar(node)}
    elif isinstance(node, yaml.SequenceNode):
        return {tag_suffix: loader.construct_sequence(node)}
    elif isinstance(node, yaml.MappingNode):
        return {tag_suffix: loader.construct_mapping(node)}
    return None

CFNLoader.add_multi_constructor('!', cfn_constructor)

def main():
    file_path = 'iac/pipeline.yml'
    
    print(f"Validating CloudFormation template: {file_path}\n")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            template = yaml.load(f, Loader=CFNLoader)
        
        if template is None:
            print("✗ Template is empty")
            sys.exit(1)
            
        print("✓ YAML syntax is valid")
    except yaml.YAMLError as e:
        print(f"✗ YAML syntax error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        sys.exit(1)
    
    # Check structure
    resources = template.get('Resources', {})
    parameters = template.get('Parameters', {})
    outputs = template.get('Outputs', {})
    
    print(f"✓ Template has {len(resources)} resources")
    print(f"✓ Template has {len(parameters)} parameters")
    print(f"✓ Template has {len(outputs)} outputs")
    
    # Verify key resources exist
    required_resources = [
        'Pipeline',
        'CodeBuildProject',
        'CodePipelineServiceRole',
        'CodeBuildServiceRole',
        'PipelineNotificationTopic'
    ]
    
    missing = []
    for res in required_resources:
        if res not in resources:
            missing.append(res)
    
    if missing:
        print(f"\n✗ Missing required resources: {', '.join(missing)}")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("\n✓ Template validation passed!")
    print("\n" + "="*60)

if __name__ == '__main__':
    main()

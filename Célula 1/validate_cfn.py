#!/usr/bin/env python3
"""Manual CloudFormation template validation"""

import yaml
import json
import sys

# Add CloudFormation intrinsic function constructors
def cfn_constructor(loader, tag_suffix, node):
    """Handle CloudFormation intrinsic functions"""
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    elif isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None

# Register CloudFormation tags
yaml.SafeLoader.add_multi_constructor('!', cfn_constructor)

def validate_yaml_syntax(file_path):
    """Validate YAML syntax"""
    try:
        with open(file_path, 'r') as f:
            template = yaml.safe_load(f)
        print(f"✓ YAML syntax is valid")
        return template
    except yaml.YAMLError as e:
        print(f"✗ YAML syntax error: {e}")
        return None

def validate_cfn_structure(template):
    """Validate basic CloudFormation structure"""
    errors = []
    warnings = []
    
    # Check required top-level keys
    if 'AWSTemplateFormatVersion' not in template:
        warnings.append("Missing AWSTemplateFormatVersion (optional but recommended)")
    
    if 'Resources' not in template:
        errors.append("Missing required 'Resources' section")
        return errors, warnings
    
    print(f"✓ Template has {len(template.get('Resources', {}))} resources")
    
    # Validate each resource
    for resource_name, resource in template.get('Resources', {}).items():
        if 'Type' not in resource:
            errors.append(f"Resource '{resource_name}' missing 'Type'")
        
        if 'Properties' not in resource and resource.get('Type') not in ['AWS::CloudFormation::WaitConditionHandle']:
            warnings.append(f"Resource '{resource_name}' has no Properties")
    
    # Check Parameters
    if 'Parameters' in template:
        print(f"✓ Template has {len(template['Parameters'])} parameters")
        for param_name, param in template['Parameters'].items():
            if 'Type' not in param:
                errors.append(f"Parameter '{param_name}' missing 'Type'")
    
    # Check Outputs
    if 'Outputs' in template:
        print(f"✓ Template has {len(template['Outputs'])} outputs")
        for output_name, output in template['Outputs'].items():
            if 'Value' not in output:
                errors.append(f"Output '{output_name}' missing 'Value'")
    
    return errors, warnings

def validate_iam_roles(template):
    """Validate IAM roles have proper structure"""
    errors = []
    resources = template.get('Resources', {})
    
    for resource_name, resource in resources.items():
        if resource.get('Type') == 'AWS::IAM::Role':
            props = resource.get('Properties', {})
            
            if 'AssumeRolePolicyDocument' not in props:
                errors.append(f"IAM Role '{resource_name}' missing AssumeRolePolicyDocument")
            
            has_policies = (
                'Policies' in props or 
                'ManagedPolicyArns' in props or
                'PermissionsBoundary' in props
            )
            
            if not has_policies:
                errors.append(f"IAM Role '{resource_name}' has no policies attached")
    
    return errors

def validate_lambda_functions(template):
    """Validate Lambda functions have required properties"""
    errors = []
    warnings = []
    resources = template.get('Resources', {})
    
    for resource_name, resource in resources.items():
        if resource.get('Type') == 'AWS::Lambda::Function':
            props = resource.get('Properties', {})
            
            required = ['Runtime', 'Handler', 'Role', 'Code']
            for req in required:
                if req not in props:
                    errors.append(f"Lambda '{resource_name}' missing required property '{req}'")
            
            # Check timeout
            timeout = props.get('Timeout', 3)
            if timeout > 900:
                errors.append(f"Lambda '{resource_name}' timeout exceeds maximum (900s)")
            
            # Check memory
            memory = props.get('MemorySize', 128)
            if memory < 128 or memory > 10240:
                errors.append(f"Lambda '{resource_name}' memory must be between 128-10240 MB")
    
    return errors, warnings

def main():
    file_path = 'iac/lambda.yml'
    
    print(f"Validating CloudFormation template: {file_path}\n")
    
    # Validate YAML syntax
    template = validate_yaml_syntax(file_path)
    if not template:
        sys.exit(1)
    
    # Validate structure
    errors, warnings = validate_cfn_structure(template)
    
    # Validate IAM roles
    iam_errors = validate_iam_roles(template)
    errors.extend(iam_errors)
    
    # Validate Lambda functions
    lambda_errors, lambda_warnings = validate_lambda_functions(template)
    errors.extend(lambda_errors)
    warnings.extend(lambda_warnings)
    
    # Print results
    print("\n" + "="*60)
    if errors:
        print(f"\n✗ Found {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✓ No errors found!")
    
    if warnings:
        print(f"\n⚠ Found {len(warnings)} warning(s):")
        for warning in warnings:
            print(f"  - {warning}")
    
    print("\n" + "="*60)
    
    if errors:
        sys.exit(1)
    else:
        print("\n✓ Template validation passed!")
        sys.exit(0)

if __name__ == '__main__':
    main()

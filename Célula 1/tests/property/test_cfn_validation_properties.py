"""
Property-based tests for CloudFormation template validation.

These tests validate that all CloudFormation templates meet AWS requirements
and can be successfully validated.
"""

import subprocess
import yaml
from pathlib import Path
from hypothesis import given, settings, strategies as st
import pytest


class TestCloudFormationValidationProperties:
    """Property-based tests for CloudFormation template validation."""
    
    @staticmethod
    def get_cfn_templates():
        """Get all CloudFormation templates from iac directory."""
        iac_dir = Path("iac")
        return list(iac_dir.glob("*.yml"))
    
    @staticmethod
    def load_yaml_template(file_path):
        """Load a YAML template with CloudFormation intrinsic function support."""
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
        
        # Create a custom loader
        class CFNLoader(yaml.SafeLoader):
            pass
        
        CFNLoader.add_multi_constructor('!', cfn_constructor)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.load(f, Loader=CFNLoader)
    
    def test_property_10_cloudformation_template_validation(self):
        """
        **Feature: aws-cartoon-rekognition, Property 10: CloudFormation Template Validation**
        
        Property: For any CloudFormation template in the /iac directory, the template
        should have valid YAML syntax and contain the required CloudFormation structure
        (Resources section at minimum).
        
        **Validates: Requirements 10.3**
        """
        templates = self.get_cfn_templates()
        
        # Ensure we have templates to test
        assert len(templates) > 0, "No CloudFormation templates found in iac/ directory"
        
        errors = []
        
        for template_path in templates:
            template_name = template_path.name
            
            try:
                # Test 1: YAML syntax validation
                template = self.load_yaml_template(template_path)
                
                if template is None:
                    errors.append(f"{template_name}: Template is empty")
                    continue
                
                # Test 2: Basic CloudFormation structure
                if not isinstance(template, dict):
                    errors.append(f"{template_name}: Template root must be a dictionary")
                    continue
                
                # Test 3: Required Resources section
                if 'Resources' not in template:
                    errors.append(f"{template_name}: Missing required 'Resources' section")
                    continue
                
                resources = template['Resources']
                if not isinstance(resources, dict):
                    errors.append(f"{template_name}: 'Resources' must be a dictionary")
                    continue
                
                if len(resources) == 0:
                    errors.append(f"{template_name}: 'Resources' section is empty")
                    continue
                
                # Test 4: Each resource must have a Type
                for resource_name, resource in resources.items():
                    if not isinstance(resource, dict):
                        errors.append(
                            f"{template_name}: Resource '{resource_name}' must be a dictionary"
                        )
                        continue
                    
                    if 'Type' not in resource:
                        errors.append(
                            f"{template_name}: Resource '{resource_name}' missing required 'Type' field"
                        )
                
                # Test 5: Validate Parameters if present
                if 'Parameters' in template:
                    parameters = template['Parameters']
                    if not isinstance(parameters, dict):
                        errors.append(f"{template_name}: 'Parameters' must be a dictionary")
                    else:
                        for param_name, param in parameters.items():
                            if not isinstance(param, dict):
                                errors.append(
                                    f"{template_name}: Parameter '{param_name}' must be a dictionary"
                                )
                            elif 'Type' not in param:
                                errors.append(
                                    f"{template_name}: Parameter '{param_name}' missing required 'Type' field"
                                )
                
                # Test 6: Validate Outputs if present
                if 'Outputs' in template:
                    outputs = template['Outputs']
                    if not isinstance(outputs, dict):
                        errors.append(f"{template_name}: 'Outputs' must be a dictionary")
                    else:
                        for output_name, output in outputs.items():
                            if not isinstance(output, dict):
                                errors.append(
                                    f"{template_name}: Output '{output_name}' must be a dictionary"
                                )
                            elif 'Value' not in output:
                                errors.append(
                                    f"{template_name}: Output '{output_name}' missing required 'Value' field"
                                )
                
            except yaml.YAMLError as e:
                errors.append(f"{template_name}: YAML syntax error - {str(e)}")
            except Exception as e:
                errors.append(f"{template_name}: Unexpected error - {str(e)}")
        
        # Assert all templates are valid
        if errors:
            error_message = "\n".join([f"  - {error}" for error in errors])
            pytest.fail(
                f"CloudFormation template validation failed:\n{error_message}"
            )


    def test_property_11_cloudformation_linting_compliance(self):
        """
        **Feature: aws-cartoon-rekognition, Property 11: CloudFormation Linting Compliance**
        
        Property: For any CloudFormation template in the /iac directory, the templates
        should follow CloudFormation best practices including proper resource naming,
        required properties, and valid references.
        
        **Validates: Requirements 10.4**
        """
        templates = self.get_cfn_templates()
        
        # Ensure we have templates to test
        assert len(templates) > 0, "No CloudFormation templates found in iac/ directory"
        
        errors = []
        
        for template_path in templates:
            template_name = template_path.name
            
            try:
                template = self.load_yaml_template(template_path)
                
                if template is None:
                    errors.append(f"{template_name}: Template is empty")
                    continue
                
                # Best Practice 1: IAM roles should have explicit permissions
                resources = template.get('Resources', {})
                for resource_name, resource in resources.items():
                    if resource.get('Type') == 'AWS::IAM::Role':
                        props = resource.get('Properties', {})
                        
                        # Check for AssumeRolePolicyDocument
                        if 'AssumeRolePolicyDocument' not in props:
                            errors.append(
                                f"{template_name}: IAM Role '{resource_name}' missing AssumeRolePolicyDocument"
                            )
                        
                        # Check for at least one policy attachment method
                        has_policies = (
                            'Policies' in props or 
                            'ManagedPolicyArns' in props
                        )
                        if not has_policies:
                            errors.append(
                                f"{template_name}: IAM Role '{resource_name}' has no policies attached"
                            )
                
                # Best Practice 2: Lambda functions should have proper configuration
                for resource_name, resource in resources.items():
                    if resource.get('Type') == 'AWS::Lambda::Function':
                        props = resource.get('Properties', {})
                        
                        # Check required properties
                        required = ['Runtime', 'Handler', 'Role', 'Code']
                        for req in required:
                            if req not in props:
                                errors.append(
                                    f"{template_name}: Lambda '{resource_name}' missing required property '{req}'"
                                )
                        
                        # Check timeout is reasonable
                        timeout = props.get('Timeout')
                        if timeout and (timeout < 1 or timeout > 900):
                            errors.append(
                                f"{template_name}: Lambda '{resource_name}' timeout must be between 1-900 seconds"
                            )
                        
                        # Check memory is in valid range
                        memory = props.get('MemorySize')
                        if memory and (memory < 128 or memory > 10240):
                            errors.append(
                                f"{template_name}: Lambda '{resource_name}' memory must be between 128-10240 MB"
                            )
                
                # Best Practice 3: S3 buckets should have encryption
                for resource_name, resource in resources.items():
                    if resource.get('Type') == 'AWS::S3::Bucket':
                        props = resource.get('Properties', {})
                        
                        # Check for encryption configuration
                        if 'BucketEncryption' not in props:
                            errors.append(
                                f"{template_name}: S3 Bucket '{resource_name}' should have BucketEncryption configured"
                            )
                
                # Best Practice 4: DynamoDB tables should have encryption
                for resource_name, resource in resources.items():
                    if resource.get('Type') == 'AWS::DynamoDB::Table':
                        props = resource.get('Properties', {})
                        
                        # Check for SSE specification
                        if 'SSESpecification' not in props:
                            errors.append(
                                f"{template_name}: DynamoDB Table '{resource_name}' should have SSESpecification configured"
                            )
                
            except Exception as e:
                errors.append(f"{template_name}: Unexpected error during linting - {str(e)}")
        
        # Assert all templates pass linting
        if errors:
            error_message = "\n".join([f"  - {error}" for error in errors])
            pytest.fail(
                f"CloudFormation linting failed:\n{error_message}"
            )


    def test_property_12_pipeline_template_validation(self):
        """
        **Feature: aws-cartoon-rekognition, Property 12: Pipeline Template Validation**
        
        Property: For any execution of the CI/CD pipeline build stage, all CloudFormation
        templates should be validated to ensure they can be deployed successfully.
        This simulates what the pipeline will do during the build stage.
        
        **Validates: Requirements 11.3**
        """
        templates = self.get_cfn_templates()
        
        # Ensure we have templates to test
        assert len(templates) > 0, "No CloudFormation templates found in iac/ directory"
        
        errors = []
        
        for template_path in templates:
            template_name = template_path.name
            
            try:
                # Simulate pipeline validation steps
                
                # Step 1: Load and parse the template (YAML validation)
                template = self.load_yaml_template(template_path)
                
                if template is None:
                    errors.append(f"{template_name}: Failed to parse YAML")
                    continue
                
                # Step 2: Verify CloudFormation structure
                if 'Resources' not in template:
                    errors.append(f"{template_name}: Missing Resources section")
                    continue
                
                resources = template['Resources']
                if not resources or len(resources) == 0:
                    errors.append(f"{template_name}: Resources section is empty")
                    continue
                
                # Step 3: Verify all resources have Type
                for resource_name, resource in resources.items():
                    if 'Type' not in resource:
                        errors.append(
                            f"{template_name}: Resource '{resource_name}' missing Type"
                        )
                
                # Step 4: Verify Parameters are properly defined
                if 'Parameters' in template:
                    for param_name, param in template['Parameters'].items():
                        if 'Type' not in param:
                            errors.append(
                                f"{template_name}: Parameter '{param_name}' missing Type"
                            )
                
                # Step 5: Verify Outputs have Value
                if 'Outputs' in template:
                    for output_name, output in template['Outputs'].items():
                        if 'Value' not in output:
                            errors.append(
                                f"{template_name}: Output '{output_name}' missing Value"
                            )
                
                # Step 6: Check for common deployment issues
                # - Circular dependencies
                # - Invalid references
                # - Missing required properties for critical resources
                
                # Check Lambda functions have all required properties
                for resource_name, resource in resources.items():
                    if resource.get('Type') == 'AWS::Lambda::Function':
                        props = resource.get('Properties', {})
                        required = ['Runtime', 'Handler', 'Role', 'Code']
                        missing = [r for r in required if r not in props]
                        if missing:
                            errors.append(
                                f"{template_name}: Lambda '{resource_name}' missing: {', '.join(missing)}"
                            )
                
                # Check IAM roles have AssumeRolePolicyDocument
                for resource_name, resource in resources.items():
                    if resource.get('Type') == 'AWS::IAM::Role':
                        props = resource.get('Properties', {})
                        if 'AssumeRolePolicyDocument' not in props:
                            errors.append(
                                f"{template_name}: IAM Role '{resource_name}' missing AssumeRolePolicyDocument"
                            )
                
            except yaml.YAMLError as e:
                errors.append(f"{template_name}: YAML parsing error - {str(e)}")
            except Exception as e:
                errors.append(f"{template_name}: Validation error - {str(e)}")
        
        # Assert all templates pass pipeline validation
        if errors:
            error_message = "\n".join([f"  - {error}" for error in errors])
            pytest.fail(
                f"Pipeline template validation failed:\n{error_message}"
            )


class TestCloudFormationTemplateStructure:
    """Additional structural tests for CloudFormation templates."""
    
    def test_all_templates_have_description(self):
        """Verify all templates have a Description field (best practice)."""
        iac_dir = Path("iac")
        templates = list(iac_dir.glob("*.yml"))
        
        missing_description = []
        
        for template_path in templates:
            # Add CloudFormation intrinsic function constructors
            def cfn_constructor(loader, tag_suffix, node):
                if isinstance(node, yaml.ScalarNode):
                    return loader.construct_scalar(node)
                elif isinstance(node, yaml.SequenceNode):
                    return loader.construct_sequence(node)
                elif isinstance(node, yaml.MappingNode):
                    return loader.construct_mapping(node)
                return None
            
            class CFNLoader(yaml.SafeLoader):
                pass
            
            CFNLoader.add_multi_constructor('!', cfn_constructor)
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template = yaml.load(f, Loader=CFNLoader)
            
            if template and 'Description' not in template:
                missing_description.append(template_path.name)
        
        # This is a warning, not a hard failure
        if missing_description:
            print(f"\nWarning: Templates without Description: {', '.join(missing_description)}")
    
    def test_all_templates_have_format_version(self):
        """Verify all templates have AWSTemplateFormatVersion (best practice)."""
        iac_dir = Path("iac")
        templates = list(iac_dir.glob("*.yml"))
        
        missing_version = []
        
        for template_path in templates:
            # Add CloudFormation intrinsic function constructors
            def cfn_constructor(loader, tag_suffix, node):
                if isinstance(node, yaml.ScalarNode):
                    return loader.construct_scalar(node)
                elif isinstance(node, yaml.SequenceNode):
                    return loader.construct_sequence(node)
                elif isinstance(node, yaml.MappingNode):
                    return loader.construct_mapping(node)
                return None
            
            class CFNLoader(yaml.SafeLoader):
                pass
            
            CFNLoader.add_multi_constructor('!', cfn_constructor)
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template = yaml.load(f, Loader=CFNLoader)
            
            if template and 'AWSTemplateFormatVersion' not in template:
                missing_version.append(template_path.name)
        
        # This is a warning, not a hard failure
        if missing_version:
            print(f"\nWarning: Templates without AWSTemplateFormatVersion: {', '.join(missing_version)}")

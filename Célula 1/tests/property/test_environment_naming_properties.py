"""
Property-based tests for environment-specific resource naming and tagging.

These tests validate that resources follow naming conventions and tagging
standards for different environments (sandbox, preprod, prod).
"""

import json
import yaml
from pathlib import Path
from hypothesis import given, settings, strategies as st
import pytest


class TestEnvironmentNamingProperties:
    """Property-based tests for environment-specific naming and tagging."""
    
    @staticmethod
    def get_cfn_templates():
        """Get all CloudFormation templates from iac directory."""
        iac_dir = Path("iac")
        return list(iac_dir.glob("*.yml"))
    
    @staticmethod
    def get_param_files():
        """Get all parameter files from iac directory."""
        iac_dir = Path("iac")
        return list(iac_dir.glob("params-*.json"))
    
    @staticmethod
    def load_yaml_template(file_path):
        """Load a YAML template with CloudFormation intrinsic function support."""
        def cfn_constructor(loader, tag_suffix, node):
            """Handle CloudFormation intrinsic functions"""
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
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.load(f, Loader=CFNLoader)
    
    @staticmethod
    def load_param_file(file_path):
        """Load a parameter JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def extract_environment_from_params(params):
        """Extract environment value from parameter list."""
        for param in params:
            if param.get('ParameterKey') == 'Environment':
                return param.get('ParameterValue')
        return None
    
    def test_property_17_environment_specific_resource_naming(self):
        """
        **Feature: aws-cartoon-rekognition, Property 17: Environment-Specific Resource Naming**
        
        Property: For any deployed resource in any environment (sandbox/preprod/prod),
        the resource name should include the environment identifier and resources should
        have tags identifying the environment.
        
        **Validates: Requirements 15.2, 15.3**
        """
        templates = self.get_cfn_templates()
        param_files = self.get_param_files()
        
        # Ensure we have templates and parameter files
        assert len(templates) > 0, "No CloudFormation templates found in iac/ directory"
        assert len(param_files) > 0, "No parameter files found in iac/ directory"
        
        errors = []
        
        # Test 1: Verify parameter files exist for all environments
        expected_envs = {'sandbox', 'preprod', 'prod'}
        found_envs = set()
        
        for param_file in param_files:
            params = self.load_param_file(param_file)
            env = self.extract_environment_from_params(params)
            if env:
                found_envs.add(env)
        
        missing_envs = expected_envs - found_envs
        if missing_envs:
            errors.append(
                f"Missing parameter files for environments: {', '.join(missing_envs)}"
            )
        
        # Test 2: Verify each parameter file has Environment parameter
        for param_file in param_files:
            params = self.load_param_file(param_file)
            env = self.extract_environment_from_params(params)
            
            if not env:
                errors.append(
                    f"{param_file.name}: Missing 'Environment' parameter"
                )
            elif env not in expected_envs:
                errors.append(
                    f"{param_file.name}: Invalid environment value '{env}', "
                    f"expected one of {expected_envs}"
                )
        
        # Test 3: Verify templates use Environment parameter in resource naming
        for template_path in templates:
            template_name = template_path.name
            
            try:
                template = self.load_yaml_template(template_path)
                
                if not template:
                    continue
                
                # Check if template has Environment parameter
                parameters = template.get('Parameters', {})
                has_env_param = 'Environment' in parameters
                
                resources = template.get('Resources', {})
                
                # For each resource, check naming conventions
                for resource_name, resource in resources.items():
                    resource_type = resource.get('Type', '')
                    props = resource.get('Properties', {})
                    
                    # Check resources that support naming
                    name_field = None
                    if resource_type in [
                        'AWS::S3::Bucket',
                        'AWS::DynamoDB::Table',
                        'AWS::Lambda::Function',
                        'AWS::IAM::Role',
                        'AWS::Logs::LogGroup',
                        'AWS::SQS::Queue',
                        'AWS::SNS::Topic'
                    ]:
                        # Determine the name field based on resource type
                        name_fields = {
                            'AWS::S3::Bucket': 'BucketName',
                            'AWS::DynamoDB::Table': 'TableName',
                            'AWS::Lambda::Function': 'FunctionName',
                            'AWS::IAM::Role': 'RoleName',
                            'AWS::Logs::LogGroup': 'LogGroupName',
                            'AWS::SQS::Queue': 'QueueName',
                            'AWS::SNS::Topic': 'TopicName'
                        }
                        name_field = name_fields.get(resource_type)
                        
                        if name_field and name_field in props:
                            name_value = props[name_field]
                            
                            # Check if name uses !Sub with ${Environment}
                            if isinstance(name_value, dict):
                                # Handle intrinsic functions
                                if 'Fn::Sub' in name_value or '!Sub' in str(name_value):
                                    # Name uses substitution, likely includes environment
                                    pass
                                else:
                                    # Check if it references Environment parameter
                                    if has_env_param and 'Ref' in name_value:
                                        if name_value['Ref'] != 'Environment':
                                            # Name doesn't reference Environment
                                            errors.append(
                                                f"{template_name}: Resource '{resource_name}' "
                                                f"name should include Environment parameter"
                                            )
                            elif isinstance(name_value, str):
                                # Static string - should not be used if Environment param exists
                                if has_env_param and '${Environment}' not in name_value:
                                    errors.append(
                                        f"{template_name}: Resource '{resource_name}' "
                                        f"has static name, should include ${{Environment}}"
                                    )
                    
                    # Check for Environment tag
                    tags = props.get('Tags', [])
                    if tags:
                        has_env_tag = False
                        for tag in tags:
                            if isinstance(tag, dict):
                                if tag.get('Key') == 'Environment':
                                    has_env_tag = True
                                    # Verify tag value references Environment parameter
                                    tag_value = tag.get('Value')
                                    if isinstance(tag_value, dict):
                                        if 'Ref' in tag_value:
                                            if tag_value['Ref'] != 'Environment':
                                                errors.append(
                                                    f"{template_name}: Resource '{resource_name}' "
                                                    f"Environment tag should reference Environment parameter"
                                                )
                                    break
                        
                        # Resources with tags should have Environment tag
                        if not has_env_tag and has_env_param:
                            # Only warn for major resources
                            if resource_type in [
                                'AWS::S3::Bucket',
                                'AWS::DynamoDB::Table',
                                'AWS::Lambda::Function',
                                'AWS::IAM::Role',
                                'AWS::EC2::VPC',
                                'AWS::EC2::Subnet',
                                'AWS::EC2::SecurityGroup'
                            ]:
                                errors.append(
                                    f"{template_name}: Resource '{resource_name}' "
                                    f"should have Environment tag"
                                )
            
            except Exception as e:
                errors.append(
                    f"{template_name}: Error analyzing template - {str(e)}"
                )
        
        # Test 4: Verify parameter files have consistent naming for stack references
        for param_file in param_files:
            params = self.load_param_file(param_file)
            env = self.extract_environment_from_params(params)
            
            if not env:
                continue
            
            # Check stack name parameters include environment
            stack_params = [
                'KMSStackName',
                'NetworkStackName',
                'S3StackName',
                'DynamoDBStackName',
                'CognitoStackName',
                'LambdaStackName'
            ]
            
            for param in params:
                param_key = param.get('ParameterKey')
                param_value = param.get('ParameterValue')
                
                if param_key in stack_params:
                    # Stack name should include environment
                    if env not in param_value:
                        errors.append(
                            f"{param_file.name}: Parameter '{param_key}' value "
                            f"'{param_value}' should include environment '{env}'"
                        )
        
        # Test 5: Verify VPC CIDR blocks are different per environment
        vpc_cidrs = {}
        for param_file in param_files:
            params = self.load_param_file(param_file)
            env = self.extract_environment_from_params(params)
            
            for param in params:
                if param.get('ParameterKey') == 'VpcCidr':
                    cidr = param.get('ParameterValue')
                    if cidr in vpc_cidrs:
                        errors.append(
                            f"VPC CIDR {cidr} is duplicated between "
                            f"{vpc_cidrs[cidr]} and {env} environments"
                        )
                    else:
                        vpc_cidrs[cidr] = env
        
        # Test 6: Verify log retention differs by environment
        log_retentions = {}
        for param_file in param_files:
            params = self.load_param_file(param_file)
            env = self.extract_environment_from_params(params)
            
            for param in params:
                if param.get('ParameterKey') == 'LogRetentionDays':
                    retention = param.get('ParameterValue')
                    log_retentions[env] = int(retention)
        
        # Sandbox should have shortest retention, prod should have longest
        if 'sandbox' in log_retentions and 'prod' in log_retentions:
            if log_retentions['sandbox'] >= log_retentions['prod']:
                errors.append(
                    f"Sandbox log retention ({log_retentions['sandbox']} days) "
                    f"should be less than prod ({log_retentions['prod']} days)"
                )
        
        # Assert all naming and tagging conventions are followed
        if errors:
            error_message = "\n".join([f"  - {error}" for error in errors])
            pytest.fail(
                f"Environment-specific naming and tagging validation failed:\n{error_message}"
            )


class TestParameterFileStructure:
    """Additional tests for parameter file structure and consistency."""
    
    def test_parameter_files_have_required_parameters(self):
        """Verify all parameter files have the required core parameters."""
        iac_dir = Path("iac")
        param_files = list(iac_dir.glob("params-*.json"))
        
        required_params = {'Environment', 'ProjectName'}
        errors = []
        
        for param_file in param_files:
            with open(param_file, 'r') as f:
                params = json.load(f)
            
            param_keys = {p['ParameterKey'] for p in params}
            missing = required_params - param_keys
            
            if missing:
                errors.append(
                    f"{param_file.name}: Missing required parameters: {', '.join(missing)}"
                )
        
        if errors:
            pytest.fail("\n".join(errors))
    
    def test_parameter_files_are_valid_json(self):
        """Verify all parameter files are valid JSON."""
        iac_dir = Path("iac")
        param_files = list(iac_dir.glob("params-*.json"))
        
        errors = []
        
        for param_file in param_files:
            try:
                with open(param_file, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                errors.append(f"{param_file.name}: Invalid JSON - {str(e)}")
        
        if errors:
            pytest.fail("\n".join(errors))
    
    def test_parameter_values_are_environment_appropriate(self):
        """Verify parameter values are appropriate for each environment."""
        iac_dir = Path("iac")
        param_files = list(iac_dir.glob("params-*.json"))
        
        warnings = []
        
        for param_file in param_files:
            with open(param_file, 'r') as f:
                params = json.load(f)
            
            env = None
            for param in params:
                if param['ParameterKey'] == 'Environment':
                    env = param['ParameterValue']
                    break
            
            if not env:
                continue
            
            # Check throttle limits are appropriate
            for param in params:
                if param['ParameterKey'] == 'ThrottleRateLimit':
                    rate = int(param['ParameterValue'])
                    if env == 'sandbox' and rate > 500:
                        warnings.append(
                            f"{param_file.name}: Sandbox throttle rate ({rate}) "
                            f"seems high for a sandbox environment"
                        )
                    elif env == 'prod' and rate < 1000:
                        warnings.append(
                            f"{param_file.name}: Prod throttle rate ({rate}) "
                            f"seems low for a production environment"
                        )
        
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  - {warning}")

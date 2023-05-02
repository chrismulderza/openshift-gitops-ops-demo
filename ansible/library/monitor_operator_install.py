#!/usr/bin/python

# Copyright: (c) 2022, Francis Viviers <fviviers@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from tempfile import NamedTemporaryFile
import subprocess

DOCUMENTATION = r'''
---
module: verify_operator_installplan

short_description: Module that installs gitops Operator and Waits for it to become ready.

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: Monitor Operator Install Success

options:
    name: Name of the operator , required=True
    namespace: Namespace of the Operator, required=True
    group: API Group of the Operator, required=False
    version: API Version of the Operator, required=False
    plural: Object Name of the Operator , required=False
    timeout: Timeout to wait for the Operator to Finish Installing, required=False

author:
    - Francis Viviers (@cainza)
'''

EXAMPLES = r'''

To test this module:

python library/monitor_operator_install.py /tmp/args.json
cat /tmp/args.json 
{
    "ANSIBLE_MODULE_ARGS": {
        "name": "openshift-gitops-operator",
        "namespace": "openshift-operators"
    }
}

'''

RETURN = r'''

{"changed": true, "invocation": {"module_args": {"name": "openshift-gitops-operator", "namespace": "openshift-operators", "group": "operators.coreos.com", "version": "v1", "plural": "operators", "timeout": 600}}}

'''

from ansible.module_utils.basic import AnsibleModule

# Import Kubernetes Requirements
import kubernetes.config
import kubernetes.client
from kubernetes.client.rest import ApiException
from pprint import pprint
import time

def verify_operator_subscription(name, namespace, group, version, plural, timeout ):

    kubernetes.config.load_kube_config()

    # Enter a context with an instance of the API kubernetes.client
    with kubernetes.client.ApiClient() as api_client:

        # Create API Instance
        api_instance = kubernetes.client.CustomObjectsApi(api_client)

        # Set default status for install
        operator_installed = False

        operatorname = "%s.%s" % (name, namespace)
        
        # Run until operator has become available
        start_time = time.time() #  Start time
        while True:

            try:
                # Calculate the time spent to run
                current_time = time.time()
                elapsed_time = current_time - start_time

                # Get / Refresh the object status
                api_response = api_instance.get_cluster_custom_object(group, version, plural, operatorname)

                for k8s_response in api_response['status']['components']['refs']:


                    if k8s_response['kind'] == "ClusterServiceVersion" and 'conditions' in k8s_response:
                        
                        # Ensure ClusterServiceVersion is Status: Installed             
                        for condition in k8s_response['conditions']:
                            if condition['type'] == 'Succeeded':
                                operator_installed = True
                                break

                        if operator_installed:
                            break           

                    elif k8s_response['kind'] == "Subscription" and 'conditions' in k8s_response:

                        for condition in k8s_response['conditions']:
                            if condition['reason'] == 'Installing' or condition['type'] == 'InstallPlanPending':
                                print ("Operator install still in progress")
                                
                if operator_installed:
                    print ("Operator Installed")
                    break
                elif elapsed_time >= timeout:
                    print("Finished iterating in: " + str(int(elapsed_time))  + " seconds")
                    #raise "Timeout waiting for Operator to become ready"
                    break
                
                # Wait between attempts
                time.sleep(5)

            except ApiException as e:
                print("Exception when calling CustomObjectsApi->get_cluster_custom_object: %s\n" % e)
                
                # Wait Longer between attempts
                time.sleep(15)
                
            except NameError as e:
                print ("%s" % e)

    return operator_installed

def get_argocd_secret():

    print ("debug")

    kubernetes.config.load_kube_config()

    # Enter a context with an instance of the API kubernetes.client
    with kubernetes.client.ApiClient() as api_client:

        print ("Busy with Secret")
        # Create API Instance
        #api_instance = kubernetes.client.CustomObjectsApi(api_client)    
        #

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True), # str | the custom resource's name
        namespace=dict(type='str', required=True), # str | the custom resource's namespace
        group=dict(type='str', required=False, default="operators.coreos.com"), # str | the custom resource's version
        version=dict(type='str', required=False, default="v1"), # str | the custom resource's plural name. For TPRs this would be lowercase plural kind.
        plural=dict(type='str', required=False, default="operators"), # str | the custom object's name
        timeout=dict(type='int', required=False, default=1200) # int | set the timeout waiting for the subscription to install
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Generate the subscription
    subscription = verify_operator_subscription(module.params['name'], module.params['namespace'], module.params['group'], module.params['version'
    ], module.params['plural'], module.params['timeout'])

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    #result['channel'] = module.params['channel']
    #result['message'] = 'goodbye'
    result['changed'] = subscription

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if result['changed'] == False:
        module.fail_json(msg='Operator install not found or valid', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
import os

import requests
from prettytable import PrettyTable

from api.generic import constants

REPORT_DIR = '/var/log/vnflcv'


def report_test_case(report_file_name, tc_exec_request, tc_input, tc_result):

    report_file_path = os.path.join(REPORT_DIR, report_file_name)
    with open(report_file_path, 'w') as report_file:

        # Write run details
        report_file.write('*** Run details ***')
        report_file.write('\n\n')
        t = PrettyTable(['Aspect', 'Value'])
        t.add_row(['Run ID', tc_exec_request['run_id'].replace('\n', '')])
        t.add_row(['Suite name', tc_exec_request['suite_name']])
        t.add_row(['TC name', tc_exec_request['tc_name']])
        t.add_row(['TC start time', tc_result['tc_start_time']])
        t.add_row(['TC end time', tc_result['tc_end_time']])
        t.add_row(['TC duration', tc_result['tc_duration']])
        report_file.write(t.get_string())
        report_file.write('\n\n')

        # Write test case environment
        report_file.write('*** Test case environment ***')
        report_file.write('\n\n')
        t = PrettyTable(['Module', 'Type'])
        t.add_row(['MANO', tc_input.get('mano', {}).get('type')])
        t.add_row(['VIM', 'openstack'])
        t.add_row(['VNF', 'vcpe'])
        t.add_row(['Traffic', tc_input.get('traffic', {}).get('type')])
        report_file.write(t.get_string())
        report_file.write('\n\n')

        t1 = PrettyTable(['Scaling type', 'Status', 'Scaling level', 'Traffic before scaling', 'Traffic after scaling'])
        print_scaling_results = False
        for direction in ['out', 'in', 'up', 'down']:
            scale_type = 'scaling_' + direction
            if bool(tc_result[scale_type]):

                # Set flag so the scaling results table will be printed
                print_scaling_results = True

                # Build the scale table row
                port_speed = tc_input['traffic']['traffic_config']['port_speed']
                status = tc_result[scale_type].get('status', 'N/A')
                scale_level = tc_result[scale_type].get('level', 'N/A')
                load_before_scaling = tc_result[scale_type].get('traffic_before', 'N/A')
                load_after_scaling = tc_result[scale_type].get('traffic_after', 'N/A')
                traffic_before_scaling = str(
                        constants.traffic_load_percent_mapping.get(load_before_scaling, 0) * port_speed / 100) + ' Mbps'
                traffic_after_scaling = str(
                        constants.traffic_load_percent_mapping.get(load_after_scaling, 0) * port_speed / 100) + ' Mbps'

                # Add the row to the table
                t1.add_row([scale_type, status, scale_level, traffic_before_scaling, traffic_after_scaling])

        # Write scaling results, if any
        if print_scaling_results:
            report_file.write('* Scaling results\n')
            report_file.write(t1.get_string())
            report_file.write('\n\n')

        # Write VNF resources
        report_file.write('* VNF resources:\n')
        for key in tc_result.get('resources', {}).keys():
            report_file.write('%s:\n' % key)
            for vnfc_id, vnfc_resources in tc_result['resources'].get(key, {}).items():
                report_file.write('Resources for VNFC %s\n' % vnfc_id)
                t = PrettyTable(['Resource type', 'Expected size', 'Actual size', 'Validation'])
                for resource_type, resource_size in vnfc_resources.items():
                    t.add_row([resource_type, resource_size, resource_size, 'OK'])
                report_file.write(t.get_string())
                report_file.write('\n\n')

        # Write test case events
        report_file.write('* Events:\n')
        t = PrettyTable(['Event', 'Duration (sec)', 'Details'])
        for event_name in tc_result.get('events', {}).keys():
            try:
                event_duration = round(tc_result['events'][event_name].get('duration'), 1)
            except TypeError:
                event_duration = 'N/A'
            event_details = tc_result['events'][event_name].get('details', '')
            t.add_row([event_name, event_duration, event_details])
        report_file.write(t.get_string())
        report_file.write('\n\n')

        # Write timestamps
        report_file.write('* Timestamps:\n')
        t = PrettyTable(['Event', 'Timestamp (epoch time)'])
        for event_name, timestamp in tc_result.get('timestamps', {}).items():
            t.add_row([event_name, timestamp])
        report_file.write(t.get_string())
        report_file.write('\n\n')

        # Write test case results
        report_file.write('*** Test case results ***')
        report_file.write('\n\n')
        t = PrettyTable(['Overall status', 'Error info'])
        t.add_row([tc_result['overall_status'], tc_result['error_info']])
        report_file.write(t.get_string())
        report_file.write('\n\n')


def kibana_report(kibana_srv, tc_exec_request, tc_input, tc_result):
    json_dict = dict()
    json_dict['run_id'] = int(tc_exec_request['run_id'])
    json_dict['suite_name'] = tc_exec_request['suite_name']
    json_dict['tc_name'] = tc_exec_request['tc_name']
    json_dict['tc_start_time'] = tc_result['tc_start_time']
    json_dict['tc_end_time'] = tc_result['tc_end_time']
    json_dict['tc_duration'] = tc_result['tc_duration']
    json_dict['tc_status'] = tc_result['overall_status']

    json_dict['environment'] = dict()
    json_dict['environment']['vim'] = 'OpenStack'
    json_dict['environment']['mano'] = tc_input['mano']['type']
    json_dict['environment']['vnf'] = 'CirrOS'
    json_dict['environment']['traffic'] = 'STCv'
    json_dict['environment']['em'] = 'None'

    durations = dict()
    durations['instantiate'] = tc_result.get('events', {}).get('instantiate_vnf', {}).get('duration')
    durations['stop'] = tc_result.get('events', {}).get('stop_vnf', {}).get('duration')
    durations['scale_out'] = tc_result.get('events', {}).get('scale_out_vnf', {}).get('duration')
    durations['scale_in'] = tc_result.get('events', {}).get('scale_in_vnf', {}).get('duration')
    durations['service_disruption'] = tc_result.get('events', {}).get('service_disruption', {}).get('duration')
    durations['traffic_fwd_disruption'] = tc_result.get('events', {}).get('traffic_fwd_disruption', {}).get('duration')

    json_dict['durations'] = dict((k, v) for k, v in durations.iteritems() if v is not None)

    requests.post(url='http://' + kibana_srv + ':9200/nfv/tc-exec', json=json_dict)


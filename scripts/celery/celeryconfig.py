broker_url='redis://10.134.12.210:6379/0'
result_backend='redis://10.134.12.210:6379/0'
timezone = 'Europe/London'

result_backend_transport_options = {
        'retry_policy': {
            'timeout': 5.0}
}
visibility_timeout = 43200

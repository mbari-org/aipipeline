import argparse

def parse_override_args(config: dict, other_args) -> argparse.Namespace:
    """
    Parse arguments that can override configuration settings in the project yaml config file
    The arguments are expected to be in a dotted format, e.g. `--redis.host=http://localhost`. which
    will update the `config['redis']['host']` field in the configuration dictionary.
    which in turn maps to the yaml configuration structure, e.g.
    `yaml
    redis:
      host: http://localhost
      port: 6379
     `
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--redis.host', type=str, help='Redis host URL')
    parser.add_argument('--redis.port', type=int, help='Redis port number')
    parser.add_argument('--data.labels', type=str, help='Comma separated list of labels to process/download. Defaults to downloading everything')
    parser.add_argument('--data.version', type=str, help='Version of the data to process/download. Comma separated list for multiple versions, e.g. Baseline,VersionA,VersionB')
    parser.add_argument('--data.download_dir', type=str, help='Directory to store downloaded/processed data')
    parser.add_argument('--data.download_args', type=str, help='Additional arguments for downloading data')
    parser.add_argument('--tator.host', type=str, help='Tator host URL')
    parser.add_argument('--tator.project', type=str, help='Tator project name')
    parser.add_argument('--sdcat.model', type=str, help='Model to use for SDCAT')
    parser.add_argument('--sdcat.ini', type=str, help='Path to SDCAT ini file')
    parser.add_argument('--vss.threshold', type=float, default=0.1, help='Threshold for VSS model predictions')
    parser.add_argument('--vss.model', type=str, help='VSS model to use. Generally a path to a model file or a model name if using HuggingFace.')

    def set_nested(config, dotted_key, value):
        keys = dotted_key.split('.')
        current = config
        for i, k in enumerate(keys):
            # handle list indexing like mounts.0.path
            if k.isdigit():
                k = int(k)
            if i == len(keys) - 1:
                current[k] = value
            else:
                if isinstance(k, int):
                    while len(current) <= k:
                        current.append({})
                    current = current[k]
                else:
                    current = current.setdefault(k, {})
    args, unknown_args = parser.parse_known_args(other_args)
    overrides = {k: v for k, v in vars(args).items() if v is not None}
    for key, val in overrides.items():
        set_nested(config, key, val)

    return config

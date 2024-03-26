import lazy_loader


__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules={
        'rdp_client',
    },
    submod_attrs={
        'rdp_client': [
            'unlock_and_unzip_file',
            'zip_and_lock_folder',
        ],
        'utils': [
            'extract_data',
            'process_important_variables',
            'config_to_title',
            'plot_trajectory'
        ],
    },
)

__all__ = ['rdp_client', 'unlock_and_unzip_file', 'zip_and_lock_folder', 'extract_data', 'process_important_variables', 'config_to_title', 'plot_trajectory']

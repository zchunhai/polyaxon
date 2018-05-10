import analytics

from tracker import TrackerService


class PublishTrackerService(TrackerService):
    def __init__(self):
        self.cluster_id = None
        self.analytics = analytics
        # Set key
        analytics.write_key = ''

    def get_cluster_id(self):
        if self.cluster_id:
            return self.cluster_id

        from clusters.models import Cluster
        cluster_uuid = Cluster.load().uuid.hex
        self.cluster_id = cluster_uuid
        return self.cluster_id

    def record_event(self, event):
        if event.event_type == 'cluster.created':
            self.analytics.identify(
                self.get_cluster_id(),
                data=event.serialize(dumps=True),
            )
        self.analytics.track(
            self.cluster_id,
            event.event_type,
            event.serialize(dumps=True),
        )

    def setup(self):
        super(PublishTrackerService, self).setup()
        self.cluster_id = self.get_cluster_id()
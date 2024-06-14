%module agora_interface


#include "AgoraBase.h"
#include "NGIAgoraAudioTrack.h" 
#include "NGIAgoraLocalUser.h"
#include "NGIAgoraMediaNodeFactory.h"
#include "NGIAgoraMediaNode.h"
#include "NGIAgoraVideoTrack.h"
#include "NGIAgoraRtcConnection.h"
#include "IAgoraService.h"
#include "IAgoraLog.h"
#include "common/file_parser/helper_h264_parser.h"
#include "common/helper.h"
#include "common/log.h"
#include "common/opt_parser.h"
#include "common/sample_common.h"
#include "common/sample_connection_observer.h"
#include "common/sample_local_user_observer.h"

import gobject
gobject.threads_init()
import gst

class ReStamp(gst.Element):
	""" Helper element to resets timestamps for buffers except for keyframes """
	
	_src_padtemplate = gst.PadTemplate ('src', 
						 gst.PAD_SRC, 
						 gst.PAD_ALWAYS, 
						 gst.caps_new_any())
	
	def __init__(self, sink_templ):
		gst.Element.__init__(self)
		self.bytestream = True
		# Sinkpad should have the same template and caps as the wrapped decoder
		self.sinkpad = gst.Pad(sink_templ, 'sink')
		self.add_pad(self.sinkpad)
		self.sinkpad.set_chain_function(self._chain)
		self.sinkpad.set_setcaps_function(self._setcaps)
		self.sinkpad.set_getcaps_function(self._getcaps)
		# Srcpad is only internal -> any caps
		self.srcpad = gst.Pad(self._src_padtemplate, 'src')
		self.add_pad(self.srcpad)

	def _setcaps(self, pad, caps):
		# We don't need to delete timestamps in avc streams. At least with mkv they are correct
		if not "byte-stream" in caps.to_string():
			self.bytestream = False
		# We simulate a decoder, so just pass on all caps negotiation
		return self.srcpad.get_peer().set_caps(caps)
		
	def _getcaps(self, pad):
		# We simulate a decoder, so just pass on all caps negotiation
		return self.srcpad.peer_get_caps()
	
	def _chain(self, pad, buf):
		# If we have byte-stream and no keyframe, delete the timestamp
		# print "Got buffer with timestamp %u, duration %u, offset %u, offset_end %u, Keyframe %r and caps: %s" % (buf.timestamp, buf.duration, buf.offset, buf.offset_end, not buf.flag_is_set(gst.BUFFER_FLAG_DELTA_UNIT), buf.caps)
		if self.bytestream and buf.flag_is_set(gst.BUFFER_FLAG_DELTA_UNIT):
			buf.timestamp = gst.CLOCK_TIME_NONE
			# print "Buffer timestamp set to gst.CLOCK_TIME_NONE"
		return self.srcpad.push(buf)
	
gobject.type_register(ReStamp)

class DecoderWrapper(gst.Bin):
	""" Wrapper for decoders to delete timestamps of non-keyframes """

	def __init__(self, *args, **kwargs):
		# init parent
		gst.Bin.__init__(self, *args, **kwargs)
		# The wrapped decoder. The child classes should set the __decoder_factory__.
		self.decoder = gst.element_factory_make(self.__decoder_factory__.get_name())
		self.add(self.decoder)
		# For every 'always' pad-template of the decoder create a ghost-pad
		for static_templ in self.__decoder_factory__.get_static_pad_templates():
			templ = static_templ.get()
			if templ.presence == gst.PAD_ALWAYS:
				if templ.direction == gst.PAD_SINK:
					# We want to delete timestamps before decoding, so we need a helper element before the sink
					element = ReStamp(templ)
					self.add(element)
					element.link(self.decoder)
					self.add_pad(gst.GhostPad(templ.name_template, element.get_pad('sink')))
				elif templ.direction == gst.PAD_SRC:
					self.add_pad(gst.GhostPad(templ.name_template, self.decoder.get_pad(templ.name_template)))
	
gobject.type_register(DecoderWrapper)

class H264DecWrapper(DecoderWrapper):
	""" Wrapper for ffdec_h264 Element """
	
	__gstdetails__ = (
		"ffdec_h264wrapper plugin",
		"Codec/Decoder/Video",
		"Wrapper for ffdec_h264, that deletes all timestamps except for keyframes",
		"Jan Schole <jan581984@web.de>")
	
	# The decoder to wrap:
	__decoder_factory__ = gst.element_factory_find('ffdec_h264')
	
	# Copy the pad-templates from the decoder:
	__gsttemplates__ = tuple([templ.get() for templ in __decoder_factory__.get_static_pad_templates()])
	
	def __init__(self, *args, **kwargs):
		DecoderWrapper.__init__(self, *args, **kwargs)
		# print "ffdec_h264wrapper initialized"

gobject.type_register(H264DecWrapper)
gst.element_register(H264DecWrapper, 'ffdec_h264wrapper', gst.RANK_PRIMARY+1)


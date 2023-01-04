
# -----------------------------------------------------------------------------
#  Face wrapper
# -----------------------------------------------------------------------------
class Face( object ):
    '''
    FT_Face wrapper

    FreeType root face class structure. A face object models a typeface in a
    font file.
    '''
    def __init__( self, path_or_stream, index = 0 ):
        '''
        Build a new Face

        :param Union[str, typing.BinaryIO] path_or_stream:
            A path to the font file or an io.BytesIO stream.

        :param int index:
               The index of the face within the font.
               The first face has index 0.
        '''
        library = get_handle( )
        face = FT_Face( )
        self._FT_Face = None
        #error = FT_New_Face( library, path_or_stream, 0, byref(face) )
        self._filebodys = []
        if hasattr(path_or_stream, "read"):
            error = self._init_from_memory(library, face, index, path_or_stream.read())
        else:
            try:
                error = self._init_from_file(library, face, index, path_or_stream)
            except UnicodeError:
                with open(path_or_stream, mode="rb") as f:
                    filebody = f.read()
                error = self._init_from_memory(library, face, index, filebody)
        if error:
            raise FT_Exception(error)
        self._index = index
        self._FT_Face = face
        self._name_strings = dict()

    def _init_from_file(self, library, face, index, path):
        u_filename = c_char_p(_encode_filename(path))
        error = FT_New_Face(library, u_filename, index, byref(face))
        return error

    def _init_from_memory(self, library, face, index, byte_stream):
        error = FT_New_Memory_Face(
            library, byte_stream, len(byte_stream), index, byref(face)
        )
        self._filebodys.append(byte_stream)  # prevent gc
        return error

    def _init_name_string_map(self):
        # build map of (nID, pID, eID, lID) keys to name string bytes
        self._name_strings = dict()

        for nidx in range(self._get_sfnt_name_count()):
            namerec = self.get_sfnt_name(nidx)
            nk = (namerec.name_id,
                    namerec.platform_id,
                    namerec.encoding_id,
                    namerec.language_id)

            self._name_strings[nk] = namerec.string

    @classmethod
    def from_bytes(cls, bytes_, index=0):
         return cls(io.BytesIO(bytes_), index)

    def __del__( self ):
        '''
        Discard  face object, as well as all of its child slots and sizes.
        '''
        if self._FT_Face is not None:
            FT_Done_Face( self._FT_Face )


    def attach_file( self, filename ):
        '''
        Attach data to a face object. Normally, this is used to read
        additional information for the face object. For example, you can attach
        an AFM file that comes with a Type 1 font to get the kerning values and
        other metrics.

        :param filename: Filename to attach

        **Note**

        The meaning of the 'attach' (i.e., what really happens when the new
        file is read) is not fixed by FreeType itself. It really depends on the
        font format (and thus the font driver).

        Client applications are expected to know what they are doing when
        invoking this function. Most drivers simply do not implement file
        attachments.
        '''

        try:
            u_filename = c_char_p(_encode_filename(filename))
            error = FT_Attach_File( self._FT_Face, u_filename )
        except UnicodeError:
            with open(filename, mode='rb') as f:
                filebody = f.read()
            parameters = FT_Open_Args()
            parameters.flags = FT_OPEN_MEMORY
            parameters.memory_base = filebody
            parameters.memory_size = len(filebody)
            parameters.stream = None
            error = FT_Attach_Stream( self._FT_Face, parameters )
            self._filebodys.append(filebody)  # prevent gc
        if error: raise FT_Exception( error)


    def set_char_size( self, width=0, height=0, hres=72, vres=72 ):
        '''
        This function calls FT_Request_Size to request the nominal size (in
        points).

        :param float width: The nominal width, in 26.6 fractional points.

        :param float height: The nominal height, in 26.6 fractional points.

        :param float hres: The horizontal resolution in dpi.

        :param float vres: The vertical resolution in dpi.

        **Note**

        If either the character width or height is zero, it is set equal to the
        other value.

        If either the horizontal or vertical resolution is zero, it is set
        equal to the other value.

        A character width or height smaller than 1pt is set to 1pt; if both
        resolution values are zero, they are set to 72dpi.

        Don't use this function if you are using the FreeType cache API.
        '''
        error = FT_Set_Char_Size( self._FT_Face, width, height, hres, vres )
        if error: raise FT_Exception( error)

    def set_pixel_sizes( self, width, height ):
        '''
        This function calls FT_Request_Size to request the nominal size (in
        pixels).

        :param width: The nominal width, in pixels.

        :param height: The nominal height, in pixels.
        '''
        error = FT_Set_Pixel_Sizes( self._FT_Face, width, height )
        if error: raise FT_Exception(error)

    def select_charmap( self, encoding ):
        '''
        Select a given charmap by its encoding tag (as listed in 'freetype.h').

        **Note**:

          This function returns an error if no charmap in the face corresponds to
          the encoding queried here.

          Because many fonts contain more than a single cmap for Unicode
          encoding, this function has some special code to select the one which
          covers Unicode best ('best' in the sense that a UCS-4 cmap is preferred
          to a UCS-2 cmap). It is thus preferable to FT_Set_Charmap in this case.
        '''
        error = FT_Select_Charmap( self._FT_Face, encoding )
        if error: raise FT_Exception(error)

    def set_charmap( self, charmap ):
        '''
        Select a given charmap for character code to glyph index mapping.

        :param charmap: A handle to the selected charmap, or an index to face->charmaps[]
        '''
        if ( type(charmap) == Charmap ):
            error = FT_Set_Charmap( self._FT_Face, charmap._FT_Charmap )
            # Type 14 is allowed to fail, to match ft2demo's behavior.
            if ( charmap.cmap_format == 14 ):
                error = 0
        else:
            # Treat "charmap" as plain number
            error = FT_Set_Charmap( self._FT_Face, self._FT_Face.contents.charmaps[charmap] )
        if error : raise FT_Exception(error)

    def get_char_index( self, charcode ):
        '''
        Return the glyph index of a given character code. This function uses a
        charmap object to do the mapping.

        :param charcode: The character code.

        **Note**:

          If you use FreeType to manipulate the contents of font files directly,
          be aware that the glyph index returned by this function doesn't always
          correspond to the internal indices used within the file. This is done
          to ensure that value 0 always corresponds to the 'missing glyph'.
        '''
        if isinstance(charcode, (str,unicode)):
            charcode = ord(charcode)
        return FT_Get_Char_Index( self._FT_Face, charcode )

    def get_glyph_name(self, agindex, buffer_max=64):
        '''
        This function is used to return the glyph name for the given charcode.

        :param agindex: The glyph index.

        :param buffer_max: The maximum number of bytes to use to store the
            glyph name.

        :param glyph_name: The glyph name, possibly truncated.

        '''
        buff = create_string_buffer(buffer_max)
        error = FT_Get_Glyph_Name(self._FT_Face, FT_UInt(agindex), byref(buff),
                                  FT_UInt(buffer_max))
        if error: raise FT_Exception(error)
        return buff.value

    def get_chars( self ):
        '''
        This generator function is used to return all unicode character
        codes in the current charmap of a given face. For each character it
        also returns the corresponding glyph index.

        :return: character code, glyph index

        **Note**:
          Note that 'agindex' is set to 0 if the charmap is empty. The
          character code itself can be 0 in two cases: if the charmap is empty
          or if the value 0 is the first valid character code.
        '''
        charcode, agindex = self.get_first_char()
        yield charcode, agindex
        while agindex != 0:
            charcode, agindex = self.get_next_char(charcode, 0)
            yield charcode, agindex

    def get_first_char( self ):
        '''
        This function is used to return the first character code in the current
        charmap of a given face. It also returns the corresponding glyph index.

        :return: Glyph index of first character code. 0 if charmap is empty.

        **Note**:

          You should use this function with get_next_char to be able to parse
          all character codes available in a given charmap. The code should look
          like this:

          Note that 'agindex' is set to 0 if the charmap is empty. The result
          itself can be 0 in two cases: if the charmap is empty or if the value 0
          is the first valid character code.
        '''
        agindex = FT_UInt()
        charcode = FT_Get_First_Char( self._FT_Face, byref(agindex) )
        return charcode, agindex.value

    def get_next_char( self, charcode, agindex ):
        '''
        This function is used to return the next character code in the current
        charmap of a given face following the value 'charcode', as well as the
        corresponding glyph index.

        :param charcode: The starting character code.

        :param agindex: Glyph index of next character code. 0 if charmap is empty.

        **Note**:

          You should use this function with FT_Get_First_Char to walk over all
          character codes available in a given charmap. See the note for this
          function for a simple code example.

          Note that 'agindex' is set to 0 when there are no more codes in the
          charmap.
        '''
        agindex = FT_UInt( 0 ) #agindex )
        charcode = FT_Get_Next_Char( self._FT_Face, charcode, byref(agindex) )
        return charcode, agindex.value

    def get_name_index( self, name ):
        '''
        Return the glyph index of a given glyph name. This function uses driver
        specific objects to do the translation.

        :param name: The glyph name.
        '''
        if not isinstance(name, bytes):
            raise FT_Exception(0x06, "FT_Get_Name_Index() expects a binary "
                               "string for the name parameter.")
        return FT_Get_Name_Index( self._FT_Face, name )

    def set_transform( self, matrix, delta ):
        '''
        A function used to set the transformation that is applied to glyph
        images when they are loaded into a glyph slot through FT_Load_Glyph.

        :param matrix: A pointer to the transformation's 2x2 matrix.
                       Use 0 for the identity matrix.

        :parm delta: A pointer to the translation vector.
                     Use 0 for the null vector.

        **Note**:

          The transformation is only applied to scalable image formats after the
          glyph has been loaded. It means that hinting is unaltered by the
          transformation and is performed on the character size given in the last
          call to FT_Set_Char_Size or FT_Set_Pixel_Sizes.

          Note that this also transforms the 'face.glyph.advance' field, but
          not the values in 'face.glyph.metrics'.
        '''
        FT_Set_Transform( self._FT_Face,
                          byref(matrix), byref(delta) )

    def select_size( self, strike_index ):
        '''
        Select a bitmap strike.

        :param strike_index: The index of the bitmap strike in the
                             'available_sizes' field of Face object.
        '''
        error = FT_Select_Size( self._FT_Face, strike_index )
        if error: raise FT_Exception( error )

    def load_glyph( self, index, flags = FT_LOAD_RENDER ):
        '''
        A function used to load a single glyph into the glyph slot of a face
        object.

        :param index: The index of the glyph in the font file. For CID-keyed
                      fonts (either in PS or in CFF format) this argument
                      specifies the CID value.

        :param flags: A flag indicating what to load for this glyph. The FT_LOAD_XXX
                      constants can be used to control the glyph loading process
                      (e.g., whether the outline should be scaled, whether to load
                      bitmaps or not, whether to hint the outline, etc).

        **Note**:

          The loaded glyph may be transformed. See FT_Set_Transform for the
          details.

          For subsetted CID-keyed fonts, 'FT_Err_Invalid_Argument' is returned
          for invalid CID values (this is, for CID values which don't have a
          corresponding glyph in the font). See the discussion of the
          FT_FACE_FLAG_CID_KEYED flag for more details.
        '''
        error = FT_Load_Glyph( self._FT_Face, index, flags )
        if error: raise FT_Exception( error )

    def load_char( self, char, flags = FT_LOAD_RENDER ):
        '''
        A function used to load a single glyph into the glyph slot of a face
        object, according to its character code.

        :param char: The glyph's character code, according to the current
                     charmap used in the face.

        :param flags: A flag indicating what to load for this glyph. The
                      FT_LOAD_XXX constants can be used to control the glyph
                      loading process (e.g., whether the outline should be
                      scaled, whether to load bitmaps or not, whether to hint
                      the outline, etc).

        **Note**:

          This function simply calls FT_Get_Char_Index and FT_Load_Glyph.
        '''

        # python 2 with ascii input
        if ( isinstance(char, str) and ( len(char) == 1 ) ):
            char = ord(char)
        # python 2 with utf8 string input
        if ( isinstance(char, str) and ( len(char) != 1 ) ):
            char = ord(char.decode('utf8'))
        # python 3 or python 2 with __future__.unicode_literals
        if ( isinstance(char, unicode) and ( len(char) == 1 ) ):
            char = ord(char)
        # allow bare integer to pass through
        error = FT_Load_Char( self._FT_Face, char, flags )
        if error: raise FT_Exception( error )


    def get_advance( self, gindex, flags ):
        '''
        Retrieve the advance value of a given glyph outline in an FT_Face. By
        default, the unhinted advance is returned in font units.

        :param gindex: The glyph index.

        :param flags: A set of bit flags similar to those used when calling
                      FT_Load_Glyph, used to determine what kind of advances
                      you need.

        :return: The advance value, in either font units or 16.16 format.

                 If FT_LOAD_VERTICAL_LAYOUT is set, this is the vertical
                 advance corresponding to a vertical layout. Otherwise, it is
                 the horizontal advance in a horizontal layout.
        '''

        padvance = FT_Fixed(0)
        error = FT_Get_Advance( self._FT_Face, gindex, flags, byref(padvance) )
        if error: raise FT_Exception( error )
        return padvance.value



    def get_kerning( self, left, right, mode = FT_KERNING_DEFAULT ):
        '''
        Return the kerning vector between two glyphs of a same face.

        :param left: The index of the left glyph in the kern pair.

        :param right: The index of the right glyph in the kern pair.

        :param mode: See FT_Kerning_Mode for more information. Determines the scale
                     and dimension of the returned kerning vector.

        **Note**:

          Only horizontal layouts (left-to-right & right-to-left) are supported
          by this method. Other layouts, or more sophisticated kernings, are out
          of the scope of this API function -- they can be implemented through
          format-specific interfaces.
        '''
        left_glyph = self.get_char_index( left )
        right_glyph = self.get_char_index( right )
        kerning = FT_Vector(0,0)
        error = FT_Get_Kerning( self._FT_Face,
                                left_glyph, right_glyph, mode, byref(kerning) )
        if error: raise FT_Exception( error )
        return kerning

    def get_format(self):
        '''
        Return a string describing the format of a given face, using values
        which can be used as an X11 FONT_PROPERTY. Possible values are
        'TrueType', 'Type 1', 'BDF', ‘PCF', ‘Type 42', ‘CID Type 1', ‘CFF',
        'PFR', and ‘Windows FNT'.
        '''

        return FT_Get_X11_Font_Format( self._FT_Face )


    def get_fstype(self):
        '''
        Return the fsType flags for a font (embedding permissions).

        The return value is a tuple containing the freetype enum name
        as a string and the actual flag as an int
        '''

        flag = FT_Get_FSType_Flags( self._FT_Face )
        for k, v in FT_FSTYPE_XXX.items():
            if v == flag:
                return k, v


    def _get_sfnt_name_count(self):
        return FT_Get_Sfnt_Name_Count( self._FT_Face )
    sfnt_name_count = property(_get_sfnt_name_count,
                doc = '''Number of name strings in the SFNT 'name' table.''')

    def get_sfnt_name( self, index ):
        '''
        Retrieve a string of the SFNT 'name' table for a given index

        :param index: The index of the 'name' string.

        **Note**:

          The 'string' array returned in the 'aname' structure is not
          null-terminated. The application should deallocate it if it is no
          longer in use.

          Use FT_Get_Sfnt_Name_Count to get the total number of available
          'name' table entries, then do a loop until you get the right
          platform, encoding, and name ID.
        '''
        name = FT_SfntName( )
        error = FT_Get_Sfnt_Name( self._FT_Face, index, byref(name) )
        if error: raise FT_Exception( error )
        return SfntName( name )

    def get_best_name_string(self, nameID, default_string='', preferred_order=None):
        '''
        Retrieve a name string given nameID. Searches available font names
        matching nameID and returns the decoded bytes of the best match.
        "Best" is defined as a preferred list of platform/encoding/languageIDs
        which can be overridden by supplying a preferred_order matching the
        scheme of 'sort_order' (see below).

        The routine will attempt to decode the string's bytes to a Python str, when the
        platform/encoding[/langID] are known (Windows, Mac, or Unicode platforms).
 
        If you prefer more control over name string selection and decoding than
        this routine provides:
            - call self._init_name_string_map()
            - use (nameID, platformID, encodingID, languageID) as a key into 
              the self._name_strings dict
       '''
        if not(self._name_strings):
            self._init_name_string_map()

        sort_order = preferred_order or (
            (3, 1, 1033),  # Microsoft/Windows/US English
            (1, 0, 0),     # Mac/Roman/English
            (0, 6, 0),     # Unicode/SMP/*
            (0, 4, 0),     # Unicode/SMP/*
            (0, 3, 0),     # Unicode/BMP/*
            (0, 2, 0),     # Unicode/10646-BMP/*
            (0, 1, 0),     # Unicode/1.1/*
        )

        # get all keys matching nameID
        keys_present = [k for k in self._name_strings.keys() if k[0] == nameID]

        if keys_present:
            # sort found keys by sort_order
            key_order = {k: v for v, k in enumerate(sort_order)}
            keys_present.sort(key=lambda x: key_order.get(x[1:4]))
            best_key = keys_present[0]
            nsbytes = self._name_strings[best_key]

            if best_key[1:3] == (3, 1) or best_key[1] == 0:
                enc = "utf-16-be"
            elif best_key[1:4] == (1, 0, 0):
                enc = "mac-roman"
            else:
                enc = "unicode_escape"

            ns = nsbytes.decode(enc)

        else:
            ns = default_string

        return ns

    def get_variation_info(self):
        '''
        Retrieves variation space information for the current face.
        '''
        if version() < (2, 8, 1):
            raise NotImplementedError("freetype-py VF support requires FreeType 2.8.1 or later")

        p_amaster = pointer(FT_MM_Var())
        error = FT_Get_MM_Var(self._FT_Face, byref(p_amaster))
        
        if error:
            raise FT_Exception(error)

        vsi = VariationSpaceInfo(self, p_amaster)

        FT_Done_MM_Var_func(p_amaster)

        return vsi

    def get_var_blend_coords(self):
        '''
        Get the current blend coordinates (-1.0..+1.0)
        '''
        vsi = self.get_variation_info()
        num_coords = len(vsi.axes)
        ft_coords = (FT_Fixed * num_coords)()
        error = FT_Get_Var_Blend_Coordinates(self._FT_Face, num_coords, byref(ft_coords))

        if error:
            raise FT_Exception(error)

        coords = tuple([ft_coords[ai]/65536.0 for ai in range(num_coords)])

        return coords

    def set_var_blend_coords(self, coords, reset=False):
        '''
        Set blend coords. Using reset=True will set all axes to
        their default coordinates.
        '''
        if reset:
            error = FT_Set_Var_Blend_Coordinates(self._FT_Face, 0, 0)
        else:
            num_coords = len(coords)
            ft_coords = [int(round(c * 65536.0)) for c in coords]
            coords_array = (FT_Fixed * num_coords)(*ft_coords)
            error = FT_Set_Var_Blend_Coordinates(self._FT_Face, num_coords, byref(coords_array))

        if error:
            raise FT_Exception(error)

    def get_var_design_coords(self):
        '''
        Get the current design coordinates
        '''
        vsi = self.get_variation_info()
        num_coords = len(vsi.axes)
        ft_coords = (FT_Fixed * num_coords)()
        error = FT_Get_Var_Design_Coordinates(self._FT_Face, num_coords, byref(ft_coords))

        if error:
            raise FT_Exception(error)

        coords = tuple([ft_coords[ai]/65536.0 for ai in range(num_coords)])

        return coords

    def set_var_design_coords(self, coords, reset=False):
        '''
        Set design coords. Using reset=True will set all axes to
        their default coordinates.
        '''
        if reset:
            error = FT_Set_Var_Design_Coordinates(self._FT_Face, 0, 0)
        
        else:
            num_coords = len(coords)
            ft_coords = [int(round(c * 65536.0)) for c in coords]
            coords_array = (FT_Fixed * num_coords)(*ft_coords)
            error = FT_Set_Var_Design_Coordinates(self._FT_Face, num_coords, byref(coords_array))

        if error:
            raise FT_Exception(error)

    def set_var_named_instance(self, instance_name):
        '''
        Set instance by name. This will work with any FreeType with variable support
        (for our purposes: v2.8.1 or later). If the actual FT_Set_Named_Instance()
        function is available (v2.9.1 or later), we use it (which, despite what you might
        expect from its name, sets instances by *index*). Otherwise we just use the coords
        of the named instance (if found) and call self.set_var_design_coords.
        '''
        have_func = freetype.version() >= (2, 9, 1)
        vsi = self.get_variation_info()

        for inst_idx, inst in enumerate(vsi.instances, start=1):
            if inst.name == instance_name:
                if have_func:
                    error = FT_Set_Named_Instance(self._FT_Face, inst_idx)
                else:
                    error = self.set_var_design_coords(inst.coords)

                if error:
                    raise FT_Exception(error)

                break

        # named instance not found; do nothing

    def _get_postscript_name( self ):
        return FT_Get_Postscript_Name( self._FT_Face )
    postscript_name = property( _get_postscript_name,
                doc = '''ASCII PostScript name of face, if available. This only
                         works with PostScript and TrueType fonts.''')

    def _has_horizontal( self ):
        return bool( self.face_flags & FT_FACE_FLAG_HORIZONTAL )
    has_horizontal = property( _has_horizontal,
               doc = '''True whenever a face object contains horizontal metrics
               (this is true for all font formats though).''')

    def _has_vertical( self ):
        return bool( self.face_flags & FT_FACE_FLAG_VERTICAL )
    has_vertical = property( _has_vertical,
             doc = '''True whenever a face object contains vertical metrics.''')

    def _has_kerning( self ):
        return bool( self.face_flags & FT_FACE_FLAG_KERNING )
    has_kerning = property( _has_kerning,
            doc = '''True whenever a face object contains kerning data that can
                     be accessed with FT_Get_Kerning.''')

    def _is_scalable( self ):
        return bool( self.face_flags & FT_FACE_FLAG_SCALABLE )
    is_scalable = property( _is_scalable,
            doc = '''true whenever a face object contains a scalable font face
                     (true for TrueType, Type 1, Type 42, CID, OpenType/CFF,
                     and PFR font formats.''')

    def _is_sfnt( self ):
        return bool( self.face_flags & FT_FACE_FLAG_SFNT )
    is_sfnt = property( _is_sfnt,
        doc = '''true whenever a face object contains a font whose format is
                 based on the SFNT storage scheme. This usually means: TrueType
                 fonts, OpenType fonts, as well as SFNT-based embedded bitmap
                 fonts.

                 If this macro is true, all functions defined in
                 FT_SFNT_NAMES_H and FT_TRUETYPE_TABLES_H are available.''')

    def _is_fixed_width( self ):
        return bool( self.face_flags & FT_FACE_FLAG_FIXED_WIDTH )
    is_fixed_width = property( _is_fixed_width,
               doc = '''True whenever a face object contains a font face that
                        contains fixed-width (or 'monospace', 'fixed-pitch',
                        etc.) glyphs.''')

    def _has_fixed_sizes( self ):
        return bool( self.face_flags & FT_FACE_FLAG_FIXED_SIZES )
    has_fixed_sizes = property( _has_fixed_sizes,
                doc = '''True whenever a face object contains some embedded
                bitmaps. See the 'available_sizes' field of the FT_FaceRec
                structure.''')

    def _has_glyph_names( self ):
        return bool( self.face_flags & FT_FACE_FLAG_GLYPH_NAMES )
    has_glyph_names = property( _has_glyph_names,
                doc = '''True whenever a face object contains some glyph names
                         that can be accessed through FT_Get_Glyph_Name.''')

    def _has_multiple_masters( self ):
        return bool( self.face_flags & FT_FACE_FLAG_MULTIPLE_MASTERS )
    has_multiple_masters = property( _has_multiple_masters,
                     doc = '''True whenever a face object contains some
                              multiple masters. The functions provided by
                              FT_MULTIPLE_MASTERS_H are then available to
                              choose the exact design you want.''')

    def _is_cid_keyed( self ):
        return bool( self.face_flags & FT_FACE_FLAG_CID_KEYED )
    is_cid_keyed = property( _is_cid_keyed,
             doc = '''True whenever a face object contains a CID-keyed
                      font. See the discussion of FT_FACE_FLAG_CID_KEYED for
                      more details.

                      If this macro is true, all functions defined in FT_CID_H
                      are available.''')

    def _is_tricky( self ):
        return bool( self.face_flags & FT_FACE_FLAG_TRICKY )
    is_tricky = property( _is_tricky,
          doc = '''True whenever a face represents a 'tricky' font. See the
                   discussion of FT_FACE_FLAG_TRICKY for more details.''')


    num_faces = property(lambda self: self._FT_Face.contents.num_faces,
          doc = '''The number of faces in the font file. Some font formats can
                   have multiple faces in a font file.''')

    face_index = property(lambda self: self._FT_Face.contents.face_index,
           doc = '''The index of the face in the font file. It is set to 0 if
                    there is only one face in the font file.''')

    face_flags = property(lambda self: self._FT_Face.contents.face_flags,
           doc = '''A set of bit flags that give important information about
                    the face; see FT_FACE_FLAG_XXX for the details.''')

    style_flags = property(lambda self: self._FT_Face.contents.style_flags,
            doc = '''A set of bit flags indicating the style of the face; see
                     FT_STYLE_FLAG_XXX for the details.''')

    num_glyphs = property(lambda self: self._FT_Face.contents.num_glyphs,
           doc = '''The number of glyphs in the face. If the face is scalable
           and has sbits (see 'num_fixed_sizes'), it is set to the number of
           outline glyphs.

           For CID-keyed fonts, this value gives the highest CID used in the
           font.''')

    family_name = property(lambda self: self._FT_Face.contents.family_name,
            doc = '''The face's family name. This is an ASCII string, usually
                     in English, which describes the typeface's family (like
                     'Times New Roman', 'Bodoni', 'Garamond', etc). This is a
                     least common denominator used to list fonts. Some formats
                     (TrueType & OpenType) provide localized and Unicode
                     versions of this string. Applications should use the
                     format specific interface to access them. Can be NULL
                     (e.g., in fonts embedded in a PDF file).''')

    style_name = property(lambda self: self._FT_Face.contents.style_name,
           doc = '''The face's style name. This is an ASCII string, usually in
                    English, which describes the typeface's style (like
                    'Italic', 'Bold', 'Condensed', etc). Not all font formats
                    provide a style name, so this field is optional, and can be
                    set to NULL. As for 'family_name', some formats provide
                    localized and Unicode versions of this string. Applications
                    should use the format specific interface to access them.''')

    num_fixed_sizes = property(lambda self: self._FT_Face.contents.num_fixed_sizes,
                doc = '''The number of bitmap strikes in the face. Even if the
                         face is scalable, there might still be bitmap strikes,
                         which are called 'sbits' in that case.''')

    def _get_available_sizes( self ):
        sizes = []
        n = self.num_fixed_sizes
        FT_sizes = self._FT_Face.contents.available_sizes
        for i in range(n):
            sizes.append( BitmapSize(FT_sizes[i]) )
        return sizes
    available_sizes = property(_get_available_sizes,
                doc = '''A list of FT_Bitmap_Size for all bitmap strikes in the
                face. It is set to NULL if there is no bitmap strike.''')

    num_charmaps = property(lambda self: self._FT_Face.contents.num_charmaps)
    def _get_charmaps( self ):
        charmaps = []
        n = self._FT_Face.contents.num_charmaps
        FT_charmaps = self._FT_Face.contents.charmaps
        for i in range(n):
            charmaps.append( Charmap(FT_charmaps[i]) )
        return charmaps
    charmaps = property(_get_charmaps,
         doc = '''A list of the charmaps of the face.''')

    #       ('generic', FT_Generic),

    def _get_bbox( self ):
        return BBox( self._FT_Face.contents.bbox )
    bbox = property( _get_bbox,
     doc = '''The font bounding box. Coordinates are expressed in font units
              (see 'units_per_EM'). The box is large enough to contain any
              glyph from the font. Thus, 'bbox.yMax' can be seen as the
              'maximal ascender', and 'bbox.yMin' as the 'minimal
              descender'. Only relevant for scalable formats.

              Note that the bounding box might be off by (at least) one pixel
              for hinted fonts. See FT_Size_Metrics for further discussion.''')

    units_per_EM = property(lambda self: self._FT_Face.contents.units_per_EM,
             doc = '''The number of font units per EM square for this
                      face. This is typically 2048 for TrueType fonts, and 1000
                      for Type 1 fonts. Only relevant for scalable formats.''')

    ascender = property(lambda self: self._FT_Face.contents.ascender,
         doc = '''The typographic ascender of the face, expressed in font
                  units. For font formats not having this information, it is
                  set to 'bbox.yMax'. Only relevant for scalable formats.''')

    descender = property(lambda self: self._FT_Face.contents.descender,
          doc = '''The typographic descender of the face, expressed in font
                   units. For font formats not having this information, it is
                   set to 'bbox.yMin'. Note that this field is usually
                   negative. Only relevant for scalable formats.''')

    height = property(lambda self: self._FT_Face.contents.height,
       doc = '''The height is the vertical distance between two consecutive
                baselines, expressed in font units. It is always positive. Only
                relevant for scalable formats.''')

    max_advance_width = property(lambda self: self._FT_Face.contents.max_advance_width,
                  doc = '''The maximal advance width, in font units, for all
                           glyphs in this face. This can be used to make word
                           wrapping computations faster. Only relevant for
                           scalable formats.''')

    max_advance_height = property(lambda self: self._FT_Face.contents.max_advance_height,
                   doc = '''The maximal advance height, in font units, for all
                            glyphs in this face. This is only relevant for
                            vertical layouts, and is set to 'height' for fonts
                            that do not provide vertical metrics. Only relevant
                            for scalable formats.''')

    underline_position = property(lambda self: self._FT_Face.contents.underline_position,
                   doc = '''The position, in font units, of the underline line
                            for this face. It is the center of the underlining
                            stem. Only relevant for scalable formats.''')

    underline_thickness = property(lambda self: self._FT_Face.contents.underline_thickness,
                    doc = '''The thickness, in font units, of the underline for
                             this face. Only relevant for scalable formats.''')


    def _get_glyph( self ):
        return GlyphSlot( self._FT_Face.contents.glyph )
    glyph = property( _get_glyph,
      doc = '''The face's associated glyph slot(s).''')

    def _get_size( self ):
        size = self._FT_Face.contents.size
        metrics = size.contents.metrics
        return SizeMetrics(metrics)
    size = property( _get_size,
     doc = '''The current active size for this face.''')

    def _get_charmap( self ):
        return Charmap( self._FT_Face.contents.charmap)
    charmap = property( _get_charmap,
        doc = '''The current active charmap for this face.''')

